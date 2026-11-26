export interface AddressSample {
  id: string;
  label: string;
  address: string;
  reference: string;
  source: string;
}

export const ADDRESS_SAMPLES: readonly AddressSample[] = [
  {
    id: 'hai-chau',
    label: 'Trung tâm Hành chính Đà Nẵng',
    address: '24 tran phu, p. thach thang, q. hai chau, da nang',
    reference: 'Số 24, Đường Trần Phú, Phường Hải Châu, Thành phố Đà Nẵng',
    source: 'https://cttdt.danangportal.gov.vn/vi/web/dng/w/chi-dao-dieu-hanh-noi-bat-cua-ubnd-thanh-pho-chu-tich-ubnd-thanh-pho-ngay-22-9',
  },
  {
    id: 'hai-phong',
    label: 'Bảo tàng Hải Phòng',
    address: '66 dien bien phu p minh khai q hong bang hai phong',
    reference: 'Số 66, Đường Điện Biên Phủ, Phường Hồng Bàng, Thành phố Hải Phòng',
    source: 'https://www.haiphong.gov.vn/tin-so-nganh/trung-bay-chuyen-de-80-nam-hai-phong-khac-ghi-loi-bac-tai-bao-tang-hai-phong-tu-ngay-16-10-den-h-984398',
  },
  {
    id: 'thanh-nien',
    label: 'Nhà Văn hóa Thanh niên TP.HCM',
    address: '04 Pham Ngoc Thach, P.Ben Nghe, Q.1, TP.HCM',
    reference: 'Số 04, Đường Phạm Ngọc Thạch, Phường Sài Gòn, Thành phố Hồ Chí Minh',
    source: 'https://hdnd.hochiminhcity.gov.vn/filemanager/userfiles/schedules/lich-tuan-02-nam-2026.pdf',
  },
  {
    id: 'hoan-kiem',
    label: 'UBND phường Hoàn Kiếm',
    address: '126 hang trong, p hang trong, q hoan kiem, ha noi',
    reference: 'Số 126, Phố Hàng Trống, Phường Hoàn Kiếm, Thành phố Hà Nội',
    source: 'https://hoankiem.hanoi.gov.vn/thong-tin-cong-khai/thong-bao-cua-ubnd-phuong-hoan-kiem-2812250904104157903.htm',
  },
  {
    id: 'can-tho',
    label: 'Bảo tàng thành phố Cần Thơ',
    address: '1 dai lo hoa binh, p ninh kieu, tp can tho',
    reference: 'Số 1, Đại lộ Hòa Bình, Phường Ninh Kiều, Thành phố Cần Thơ',
    source: 'https://baotangso.web.app/about.html',
  },
  {
    id: 'ubnd-hcm',
    label: 'Văn phòng UBND TP.HCM',
    address: '86 le thanh ton - p.ben nghe - q1 - tphcm',
    reference: 'Số 86, Đường Lê Thánh Tôn, Phường Sài Gòn, Thành phố Hồ Chí Minh',
    source: 'https://congbao.hochiminhcity.gov.vn/DKC.MFiles.CB/Gazette/DownLoadFileResult/49000',
  },
  {
    id: 'giang-vo',
    label: 'UBND phường Giảng Võ',
    address: '525 kim ma, p ngoc khanh, q ba dinh, ha noi',
    reference: 'Số 525, Phố Kim Mã, Phường Giảng Võ, Thành phố Hà Nội',
    source: 'https://xdcs.cdnchinhphu.vn/446259493575335936/2025/6/26/danh-sach-126-xa-17509016620211864713480.pdf',
  },
  {
    id: 'ha-long',
    label: 'Ban Quản lý Vịnh Hạ Long',
    address: '166 le thanh tong, p hong gai, quang ninh',
    reference: 'Số 166, Đường Lê Thánh Tông, Phường Hồng Gai, Tỉnh Quảng Ninh',
    source: 'https://uongbi.gov.vn/ckfinder/userfiles/files/Ph%E1%BB%A5%20l%E1%BB%A5c%20kem%20Q%C4%90%202040%20ma%20dinh%20danh.pdf',
  }
];
