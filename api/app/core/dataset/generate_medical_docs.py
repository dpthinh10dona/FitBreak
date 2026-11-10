"""
Script to generate standard clinical and ergonomic knowledge documents for FitBreak RAG.
Creates both .docx (OpenXML standard) and .md knowledge files.
"""

import os
import zipfile
import xml.sax.saxutils as saxutils
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parent / "medical_knowledge"
DATASET_DIR.mkdir(parents=True, exist_ok=True)


def esc(text: str) -> str:
    """Escapes XML entities."""
    return saxutils.escape(str(text))


def build_docx(file_path: Path, title: str, sections: list) -> None:
    """Build a standard OpenXML .docx file."""
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '    <Default Extension="xml" ContentType="application/xml"/>\n'
        '    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
        '</Types>'
    )

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
        '</Relationships>'
    )

    body_xml = []
    # Title (Heading 1)
    body_xml.append(
        '<w:p>'
        '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        f'<w:r><w:rPr><w:b/><w:sz w:val="36"/></w:rPr><w:t>{esc(title)}</w:t></w:r>'
        '</w:p>'
    )

    for sec in sections:
        h2 = sec.get("h2")
        if h2:
            body_xml.append(
                '<w:p>'
                '<w:pPr><w:pStyle w:val="Heading2"/></w:pPr>'
                f'<w:r><w:rPr><w:b/><w:sz w:val="28"/></w:rPr><w:t>{esc(h2)}</w:t></w:r>'
                '</w:p>'
            )

        for p in sec.get("paragraphs", []):
            body_xml.append(f'<w:p><w:r><w:t>{esc(p)}</w:t></w:r></w:p>')

        for b in sec.get("bullets", []):
            body_xml.append(
                '<w:p>'
                '<w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>'
                f'<w:r><w:t>{esc(b)}</w:t></w:r>'
                '</w:p>'
            )

        table = sec.get("table")
        if table:
            tbl_xml = ['<w:tbl>']
            for row in table:
                tbl_xml.append('<w:tr>')
                for cell in row:
                    tbl_xml.append(f'<w:tc><w:p><w:r><w:t>{esc(cell)}</w:t></w:r></w:p></w:tc>')
                tbl_xml.append('</w:tr>')
            tbl_xml.append('</w:tbl>')
            body_xml.append(''.join(tbl_xml))

    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        f'    <w:body>{"".join(body_xml)}</w:body>\n'
        '</w:document>'
    )

    with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc_xml)
    print(f"-> Tạo thành công file DOCX: {file_path.name}")


def main():
    print("Đang khởi tạo các tài liệu tri thức y khoa lâm sàng cho FitBreak...")

    # 1. DOCX 1: Công thái học và Cơ xương khớp
    build_docx(
        DATASET_DIR / "01_Huong_Dan_Cong_Thai_Hoc_Va_Co_Xuong_Khop_FitBreak.docx",
        "Hướng dẫn Công thái học & Chăm sóc Cơ Xương Khớp FitBreak",
        [
            {
                "h2": "1. Hội chứng Cổ Vai Gáy (Cervical Pain / Text Neck)",
                "paragraphs": [
                    "Hội chứng cổ vai gáy là rối loạn cơ xương khớp phổ biến nhất ở học sinh và nhân viên văn phòng do duy trì tư thế cúi đầu nhìn màn hình điện thoại hoặc máy tính trong thời gian dài mà không nghỉ giải lao.",
                ],
                "bullets": [
                    "Nguyên nhân cơ sinh học: Nghiêng đầu về trước 30 độ làm tăng tải trọng lên đốt sống cổ lên đến 18kg; nghiêng 60 độ tương đương 27kg tải trọng đè nén liên tục.",
                    "Triệu chứng điển hình: Cảm giác căng cứng, nhức mỏi vùng cơ thang, cơ nâng vai, hạn chế tầm vận động xoay cổ sang hai bên.",
                    "Giải pháp can thiệp FitBreak: Thực hiện bài tập Active Break mỗi 45 phút: Cằm thụt (Chin-tuck) 10 lần, kéo giãn cơ thang bên cạnh mỗi bên 15 giây, xoay khớp vai tròn 10 lần ra sau.",
                    "Khuyến nghị thể lực: Chuyển cường độ bài tập sang mức Light (Vận động nhẹ / Phục hồi), tránh tập tạ vai hoặc gập bụng gây gồng cơ cổ.",
                    "Dấu hiệu nguy hiểm (Red Flags): Cơn đau lan dọc xuống cánh tay, tê buốt bàn tay hoặc ngón tay, yếu cơ cầm nắm đồ vật -> Cần tới khám chuyên khoa Thần kinh - Cột sống ngay.",
                ],
            },
            {
                "h2": "2. Đau Thắt Lưng Cột Sống Do Ngồi Lâu (Low Back Pain)",
                "paragraphs": [
                    "Áp lực lên đĩa đệm cột sống thắt lưng khi ngồi cong lưng cao hơn 1.5 lần so với khi đứng thẳng và cao hơn 2.5 lần so với khi nằm nghỉ ngơi.",
                ],
                "bullets": [
                    "Tư thế công thái học chuẩn: Chân chạm đất vững chãi, khớp gối vuông góc 90 độ, có gối hoặc đệm tựa thắt lưng, màn hình máy tính ngang tầm mắt cách 50-70 cm.",
                    "Bài tập giải tỏa tức thì: Đứng dậy đi lại 1-2 phút, duỗi cột sống nhẹ nhàng ra sau (McKenzie extension), kéo giãn cơ gấp hông (Hip flexor stretch).",
                    "Dấu hiệu cảnh báo nguy hiểm (Red Flags): Đau buốt dữ dội lan xuống mặt sau đùi (dây thần kinh tọa), mất cảm giác vùng hội âm, rối loạn tiêu tiểu -> Cần cấp cứu ngoại thần kinh.",
                ],
                "table": [
                    ["Tiêu chí đánh giá", "Tư thế sai gây hại", "Tư thế chuẩn công thái học FitBreak"],
                    ["Tầm nhìn màn hình", "Cúi gập cổ nhìn xuống", "Ngang tầm mắt (cách mắt 50-70 cm)"],
                    ["Vị trí cổ tay", "Bị gập tì đè mép bàn", "Thẳng hàng với cẳng tay, có đệm đỡ"],
                    ["Góc gối và đùi", "Bắt chéo chân, gập sâu", "Góc gối 90-100 độ, bàn chân đặt phẳng"],
                ],
            },
            {
                "h2": "3. Hội chứng Ống Cổ Tay (Carpal Tunnel Syndrome)",
                "paragraphs": [
                    "Tình trạng chèn ép dây thần kinh giữa tại cổ tay do dùng chuột máy tính hoặc gõ bàn phím sai cách liên tục nhiều giờ.",
                ],
                "bullets": [
                    "Biểu hiện: Tê rần, châm chích ngón cái, ngón trỏ và ngón giữa, đau tăng về đêm.",
                    "Xử trí tại nhà: Kê đệm cổ tay công thái học, ngưng gõ phím sau mỗi 30 phút, xoay cổ tay nhẹ nhàng theo vòng tròn.",
                ],
            },
        ],
    )

    # 2. DOCX 2: Phác đồ Dinh dưỡng Lâm sàng & Tiêu hóa
    build_docx(
        DATASET_DIR / "02_Phac_Do_Dinh_Duong_Va_Tieu_Hoa_FitBreak.docx",
        "Phác đồ Dinh dưỡng Lâm sàng & Rối loạn Tiêu hóa FitBreak",
        [
            {
                "h2": "1. Phác đồ Xử trí Rối loạn Tiêu hóa & Tiêu chảy Cấp tại nhà",
                "paragraphs": [
                    "Rối loạn tiêu hóa cấp tính ở thanh thiếu niên và người làm việc tĩnh tại thường do ngộ độc thực phẩm nhẹ, nhiễm khuẩn đường ruột hoặc căng thẳng stress thần kinh (IBS).",
                ],
                "bullets": [
                    "Nguyên tắc vàng: Bù nước và bù điện giải là ưu tiên số một. Uống dung dịch Oresol đúng tỷ lệ hoặc nước dừa tươi bù khoáng, uống từng ngụm nhỏ 100-150ml sau mỗi lần đi tiêu.",
                    "Áp dụng chế độ ăn BRAT: Banana (Chuối - giàu kali bù điện giải), Rice (Cơm trắng hoặc cháo loãng - dễ tiêu hóa), Applesauce (Táo hấp hoặc sốt táo - chứa pectin làm đặc phân), Toast (Bánh mì nướng - hấp thụ axit dịch vị thừa).",
                    "Các món cấm tuyệt đối: Sữa và sản phẩm từ sữa có lactose, caffeine, trà đặc, nước ngọt có ga, thức ăn nhiều dầu mỡ chiên xào, thức ăn cay nồng.",
                    "Chỉ định thể lực: Nghỉ ngơi hoàn toàn hoặc chỉ vận động nhẹ mức Light, tuyệt đối không tập cardio hoặc bài tập gắng sức gây mất nước.",
                    "Dấu hiệu cảnh báo nguy hiểm (Red Flags): Sốt cao trên 38.5 độ C, nôn ói liên tục không uống được nước, đi ngoài ra máu hoặc phân đen như bã cà phê, dấu hiệu mất nước nặng (môi khô nứt nẻ, mắt trũng, tiểu ít sẫm màu) -> Phải tới bệnh viện ngay.",
                ],
            },
            {
                "h2": "2. Viêm Trào Ngược Dạ Dày Thực Quản (GERD) & Đau Thượng Vị",
                "paragraphs": [
                    "Áp lực công việc cùng thói quen ăn uống vội vàng, bỏ bữa dẫn đến tăng tiết axit dạ dày và trào ngược dịch vị lên thực quản.",
                ],
                "bullets": [
                    "Triệu chứng: Nóng rát sau xương ức, ợ chua, đau âm ỉ thượng vị, cảm giác vướng ở cổ họng.",
                    "Điều chỉnh dinh dưỡng: Tránh nằm ngay sau khi ăn ít nhất 2 giờ; chia nhỏ khẩu phần 4-5 bữa/ngày; hạn chế nước cam, chanh, tương ớt, chocolate, đồ uống có cồn.",
                    "Lưu ý tập luyện: Tránh các bài tập gập bụng (sit-ups, crunches) và nâng tạ nặng làm tăng áp lực ổ bụng.",
                ],
            },
            {
                "h2": "3. Cân bằng Năng lượng Calo & Vi chất Học đường",
                "paragraphs": [
                    "Hướng dẫn duy trì thâm hụt calo nhẹ nhàng (300-500 kcal/ngày) cho người béo phì hoặc duy trì cân nặng hợp lý.",
                ],
                "bullets": [
                    "Cân đối đa lượng: 45-55% Carbs phức hợp (gạo lứt, khoai lang, yến mạch), 20-25% Protein chất lượng cao (ức gà, cá, đậu phụ, trứng), 20-25% Chất béo lành mạnh (dầu ô liu, các loại hạt).",
                    "Nước uống: Tối thiểu 0.4 lít nước / 10kg trọng lượng cơ thể mỗi ngày.",
                ],
            },
        ],
    )

    # 3. MD 1: Cẩm nang Y học Thể thao Micro-Workouts
    md_sports = """# Cẩm nang Y học Thể thao & Micro-Workouts FitBreak
Nguồn: Phác đồ Y học Thể thao Thực hành & Phục hồi Thể chất FitBreak

## 1. Phòng ngừa & Xử trí Đau cơ Sau Tập (DOMS)
- **Nhận diện**: Đau nhức cơ bắp ê ẩm, căng tức xuất hiện sau buổi tập từ 12 đến 48 giờ (Delayed Onset Muscle Soreness - DOMS).
- **Cơ chế**: Do các vi tổn thương sợi cơ kích thích phản ứng tái tạo và xây dựng cơ bắp mới, đây là hiện tượng sinh lý bình thường.
- **Xử trí tại nhà**: 
  - Tắm nước ấm thư giãn, ngâm bồn muối Epsom để thả lỏng cơ.
  - Thực hiện giãn cơ tĩnh (Static Stretching) nhẹ nhàng 15-30 giây mỗi nhóm cơ.
  - Uống đủ nước và bổ sung điện giải giàu Kali, Magie (chuối chín, nước dừa, các loại hạt).
- **Khuyến nghị thể lực**: Điều chỉnh lịch tập sang cường độ 'Light' (phục hồi chủ động), tập trung vào các nhóm cơ khác chưa bị mỏi.
- **Dấu hiệu nguy hiểm (Red Flags)**: Nước tiểu sẫm màu như màu trà đặc hoặc xì dầu (nghi ngờ tiêu cơ vân cấp tính - Rhabdomyolysis), sưng to bất thường ở bắp cơ -> Phải nhập viện cấp cứu ngay.

## 2. Xử trí Chuột Rút Cấp tính khi Vận động
- **Xử trí tức thì**: Dừng ngay vận động, kéo giãn từ từ cơ đang co rút theo hướng ngược lại và giữ nguyên 20-30 giây.
- **Bổ sung**: Uống nước ấm pha chút muối hoặc nước khoáng điện giải. Tránh xoa bóp quá thô bạo gây dập sợi cơ đang căng cứng.
"""
    with open(DATASET_DIR / "03_Cam_Nang_Y_Hoc_The_Thao_Micro_Workouts.md", "w", encoding="utf-8") as f:
        f.write(md_sports)
    print("-> Tạo thành công file MD: 03_Cam_Nang_Y_Hoc_The_Thao_Micro_Workouts.md")

    # 4. MD 2: Hướng dẫn Thị giác và Giấc ngủ Văn phòng
    md_vision = """# Hướng dẫn Thị giác & Vệ sinh Giấc ngủ Văn phòng FitBreak
Nguồn: Tiêu chuẩn Chăm sóc Sức khỏe Thần kinh & Thị giác Học đường

## 1. Hội chứng Thị giác Màn hình (Computer Vision Syndrome - CVS)
- **Triệu chứng**: Khô mắt, rát mắt, nhìn mờ tạm thời, chảy nước mắt, nhức đầu sau 2-3 tiếng liên tục nhìn màn hình.
- **Quy tắc vàng 20-20-20**:
  - Cứ mỗi **20 phút** nhìn màn hình.
  - Hãy nhìn ra xa một vật cách xa ít nhất **20 feet (khoảng 6 mét)**.
  - Duy trì nhìn xa trong vòng ít nhất **20 giây** kết hợp chớp mắt chậm 10 lần.
- **Điều chỉnh môi trường**: Đặt màn hình thấp hơn tầm mắt 10-15 độ, chỉnh độ sáng màn hình tương đồng với ánh sáng phòng, sử dụng nước mắt nhân tạo không chất bảo quản nếu khô mắt nhiều.

## 2. Vệ sinh Giấc ngủ (Sleep Hygiene) cho Học sinh & Dân Văn phòng
- **Nguyên tắc**: Tắt hoặc tránh nhìn màn hình điện thoại/máy tính ít nhất 60 phút trước khi đi ngủ để tránh ánh sáng xanh ức chế hormone Melatonin.
- **Nhiệt độ phòng**: Giữ phòng ngủ thoáng mát (khoảng 24-26 độ C), hạn chế tiếng ồn và ánh sáng.
- **Dinh dưỡng bổ trợ**: Uống 1 ly trà hoa cúc ấm hoặc sữa hạt ấm trước khi ngủ 45 phút, tránh caffeine và trà sau 14h chiều.
"""
    with open(DATASET_DIR / "04_Huong_Dan_Thi_Giac_Va_Giac_Ngu_Van_Phong.md", "w", encoding="utf-8") as f:
        f.write(md_vision)
    print("-> Tạo thành công file MD: 04_Huong_Dan_Thi_Giac_Va_Giac_Ngu_Van_Phong.md")

    print("\nHoàn tất tạo bộ tài liệu tri thức y khoa chuẩn!")


if __name__ == "__main__":
    main()
