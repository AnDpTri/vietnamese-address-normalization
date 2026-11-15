"""Bộ nhận diện ký tự CPU: residual dilated CNN và CRF BIO có ràng buộc.

Unicode NFC có ánh xạ về chuỗi gốc. Không cắt ngắn địa chỉ âm thầm.
Điểm emission dùng làm đặc trưng ranker, không phải xác suất đúng toàn câu.
"""

import hashlib
import math
import unicodedata
from pathlib import Path

import torch
from torch import nn

from .crf_chi_tiet import NguCanhCRF
from .tach_phan_con import FIELDS
from .tien_xu_ly import Token, token_co_vi_tri

from .nhan import ROLES, TAGS, TAG_ID, tag_spans
from .ngu_canh_neural import NguCanhChar
from .tien_xu_ly import nfc_offsets, gom_khoang_trang






class LinearCRF(nn.Module):
    """NLL CRF với nhãn một phần: log Z - log Z(nhãn được phép)."""
    def __init__(self):
        super().__init__()
        n = len(TAGS)
        self.transitions = nn.Parameter(torch.zeros(n, n))  # from, to
        self.start = nn.Parameter(torch.zeros(n))
        self.end = nn.Parameter(torch.zeros(n))
        legal = torch.ones(n, n, dtype=torch.bool)
        start_ok = torch.ones(n, dtype=torch.bool)
        for j, tag in enumerate(TAGS):
            if tag.startswith('I-'):
                start_ok[j] = False
                for i, prev in enumerate(TAGS):
                    legal[i, j] = prev in ('B-' + tag[2:], tag)
        self.register_buffer('legal', legal)
        self.register_buffer('start_ok', start_ok)

    def partition(self, emissions, mask):
        trans = self.transitions.masked_fill(~self.legal, -10000.)
        score = self.start.masked_fill(~self.start_ok, -10000.) + emissions[:, 0]
        for t in range(1, emissions.size(1)):
            nxt = torch.logsumexp(score.unsqueeze(2) + trans.unsqueeze(0), dim=1) + emissions[:, t]
            score = torch.where(mask[:, t, None], nxt, score)
        return torch.logsumexp(score + self.end, dim=1)

    def loss(self, emissions, mask, allowed):
        constrained = emissions.masked_fill(~allowed, -10000.)
        z = self.partition(torch.cat([emissions, constrained]), torch.cat([mask, mask]))
        full, partial = z.chunk(2)
        return ((full - partial) / mask.sum(1)).mean()

    def decode(self, emissions):
        """CPU/numpy Viterbi, một câu, tránh overhead torch ở mỗi ký tự."""
        import numpy as np
        e = emissions.detach().cpu().numpy()
        trans = self.transitions.detach().cpu().numpy().copy()
        trans[~self.legal.cpu().numpy()] = -10000.
        score = self.start.detach().cpu().numpy().copy() + e[0]
        score[~self.start_ok.cpu().numpy()] = -10000.
        history = []
        for row in e[1:]:
            grid = score[:, None] + trans
            previous = grid.argmax(0)
            history.append(previous)
            score = grid[previous, np.arange(len(TAGS))] + row
        best = int((score + self.end.detach().cpu().numpy()).argmax())
        path = [best]
        for previous in reversed(history):
            best = int(previous[best])
            path.append(best)
        return path[::-1]


class ResidualBlock(nn.Module):
    def __init__(self, channels, dilation, dropout):
        super().__init__()
        self.conv1 = nn.Conv1d(channels, channels, 3, padding=dilation, dilation=dilation)
        self.conv2 = nn.Conv1d(channels, channels, 3, padding=dilation, dilation=dilation)
        self.drop = nn.Dropout(dropout)

    def forward(self, x, mask):
        y = self.drop(torch.relu(self.conv1(x))) * mask
        y = self.drop(self.conv2(y)) * mask
        return torch.relu(x + y) * mask


class CharCNNCRF(nn.Module):
    def __init__(self, vocabulary_size, embedding=64, channels=96, dilations=(1, 2, 4, 8, 16, 32), dropout=.15):
        super().__init__()
        self.embedding = nn.Embedding(vocabulary_size, embedding, padding_idx=0)
        self.project = nn.Conv1d(embedding, channels, 1)
        self.blocks = nn.ModuleList(ResidualBlock(channels, d, dropout) for d in dilations)
        self.classifier = nn.Conv1d(channels, len(TAGS), 1)
        self.crf = LinearCRF()

    def forward(self, ids, mask):
        m = mask[:, None].to(self.embedding.weight.dtype)
        x = self.project(self.embedding(ids).transpose(1, 2)) * m
        for block in self.blocks:
            x = block(x, m)
        return self.classifier(x).transpose(1, 2)




class BoTachCharCNN:
    phien_ban = 'char_cnn_crf_v1'
    bao_ve_chi_tiet = False

    def __init__(self, model_path, threads=1):
        if threads < 1:
            raise ValueError('threads phải >= 1')
        torch.set_num_threads(threads)
        path = Path(model_path)
        self.ma_bam = hashlib.sha256(path.read_bytes()).hexdigest()
        checkpoint = torch.load(path, map_location='cpu', weights_only=True)
        if checkpoint['tags'] != TAGS or checkpoint['format'] != 1:
            raise ValueError('Schema mô hình Char-CNN không tương thích')
        self.vocab = checkpoint['vocab']
        self.model = CharCNNCRF(len(self.vocab) + 2, **checkpoint['config'])
        self.model.load_state_dict(checkpoint['state_dict'])
        self.model.eval()

    def chuan_bi_chuoi(self, raw):
        text, offsets = nfc_offsets(raw)
        text, offsets = gom_khoang_trang(text, offsets)
        if len(text) > 2048:
            raise ValueError('Bản thử giới hạn 2048 ký tự; đầu vào chưa được xử lý, không cắt ngắn')
        if not text:
            return NguCanhChar(raw, text, offsets, [], torch.empty(0, len(TAGS)))
        alpha = [c for c in text if c.isalpha()]
        is_all_caps = len(alpha) > 8 and (sum(c.isupper() for c in alpha) / len(alpha) > 0.7)
        c_source = text.title() if (is_all_caps and len(text.title()) == len(text)) else text
        ids = torch.tensor([[self.vocab.get(c, 1) for c in c_source]], dtype=torch.long)
        with torch.inference_mode():
            logits = self.model(ids, torch.ones_like(ids, dtype=torch.bool))[0]
            tags = [TAGS[i] for i in self.model.crf.decode(logits)]
            lp = torch.log_softmax(logits, -1)
        return NguCanhChar(raw, text, offsets, tags, lp)
