"""Kiểm tra dữ liệu được lưu trong chế độ nhật ký Render."""

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nhat_ky


class TestNhatKyRender(unittest.TestCase):
    def test_render_chi_luu_dia_chi_khi_bao_sai(self):
        stdout = io.StringIO()
        dia_chi = "ĐỊA CHỈ MẪU"
        with TemporaryDirectory() as thu_muc:
            with patch.dict(os.environ, {"AMC_LOG": "render", "AMC_LOG_DIR": thu_muc}), redirect_stdout(stdout):
                id_chuan_hoa = nhat_ky.ghi("chuan_hoa", {
                    "nguon": "hang_loat",
                    "status": "needs_review",
                    "input": dia_chi,
                    "id": dia_chi,
                    "result": {"dia_chi_chuan": dia_chi},
                    "chan_doan": {"token": [dia_chi]},
                })
                nhat_ky.ghi_loi(dia_chi, ValueError(dia_chi))
                id_bao_sai = nhat_ky.ghi("bao_sai", {
                    "input": dia_chi,
                    "ghi_chu": "Sai tên phường\nKiểm tra lại",
                    "ref_log_id": id_chuan_hoa,
                })
                nhat_ky.ghi("bao_sai", {"input": dia_chi, "ref_log_id": "mã tự nhập"})

            tep = list(Path(thu_muc).glob("phien_*.jsonl"))
            self.assertEqual(len(tep), 1)
            da_luu = [json.loads(s) for s in tep[0].read_text(encoding="utf-8").splitlines()]

        dong = stdout.getvalue().splitlines()
        self.assertEqual(len(dong), 4)
        self.assertNotIn(dia_chi, dong[0])
        self.assertNotIn(dia_chi, dong[1])
        ban_sao = [json.loads(s.removeprefix("AMC_LOG ")) for s in dong]
        self.assertTrue(all(s.pop("luu_tep") for s in ban_sao))
        self.assertEqual(da_luu, ban_sao)
        chuan_hoa, loi, bao_sai, ref_khong_hop_le = da_luu
        self.assertEqual(chuan_hoa["status"], "needs_review")
        self.assertEqual(loi["loai_loi"], "ValueError")
        self.assertEqual(bao_sai["ref_log_id"], id_chuan_hoa)
        self.assertEqual(bao_sai["log_id"], id_bao_sai)
        self.assertEqual(bao_sai["input"], dia_chi)
        self.assertEqual(bao_sai["ghi_chu"], "Sai tên phường\nKiểm tra lại")
        self.assertNotIn("ref_log_id", ref_khong_hop_le)

    def test_render_giu_ban_sao_khi_tep_khong_ghi_duoc(self):
        stdout = io.StringIO()
        with TemporaryDirectory() as thu_muc:
            tep = Path(thu_muc) / "tep"
            tep.touch()
            with patch.dict(os.environ, {"AMC_LOG": "render", "AMC_LOG_DIR": str(tep)}), redirect_stdout(stdout):
                log_id = nhat_ky.ghi("chuan_hoa", {"status": "processed"})
        ban_sao = json.loads(stdout.getvalue().removeprefix("AMC_LOG "))
        self.assertFalse(ban_sao["luu_tep"])
        self.assertEqual(ban_sao["log_id"], log_id)

    def test_tat_nhat_ky(self):
        stdout = io.StringIO()
        with patch.dict(os.environ, {"AMC_LOG": "0"}), redirect_stdout(stdout):
            self.assertIsNone(nhat_ky.ghi("bao_sai", {"input": "ĐỊA CHỈ MẪU"}))
        self.assertEqual(stdout.getvalue(), "")
