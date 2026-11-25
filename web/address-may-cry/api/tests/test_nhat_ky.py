"""Kiểm tra dữ liệu được lưu trong chế độ nhật ký Render."""

import io
import json
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import nhat_ky


class TestNhatKyRender(unittest.TestCase):
    def test_render_chi_luu_dia_chi_khi_bao_sai(self):
        stdout = io.StringIO()
        dia_chi = "ĐỊA CHỈ MẪU"
        with patch.dict(os.environ, {"AMC_LOG": "render"}), redirect_stdout(stdout):
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

        dong = stdout.getvalue().splitlines()
        self.assertEqual(len(dong), 4)
        self.assertNotIn(dia_chi, dong[0])
        self.assertNotIn(dia_chi, dong[1])
        chuan_hoa, loi, bao_sai, ref_khong_hop_le = [
            json.loads(s.removeprefix("AMC_LOG ")) for s in dong
        ]
        self.assertEqual(chuan_hoa["status"], "needs_review")
        self.assertEqual(loi["loai_loi"], "ValueError")
        self.assertEqual(bao_sai["ref_log_id"], id_chuan_hoa)
        self.assertEqual(bao_sai["log_id"], id_bao_sai)
        self.assertEqual(bao_sai["input"], dia_chi)
        self.assertEqual(bao_sai["ghi_chu"], "Sai tên phường\nKiểm tra lại")
        self.assertNotIn("ref_log_id", ref_khong_hop_le)

    def test_tat_nhat_ky(self):
        stdout = io.StringIO()
        with patch.dict(os.environ, {"AMC_LOG": "0"}), redirect_stdout(stdout):
            self.assertIsNone(nhat_ky.ghi("bao_sai", {"input": "ĐỊA CHỈ MẪU"}))
        self.assertEqual(stdout.getvalue(), "")
