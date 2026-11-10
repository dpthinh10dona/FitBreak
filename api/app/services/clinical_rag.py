"""
Clinical RAG Service for FitBreak Telehealth Doctor.
Provides medical guidelines, sports medicine protocols, and clinical nutrition evidence
for RAG-First clinical advisor responses.
"""

from typing import List, Dict, Any
import re

CLINICAL_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "id": "med_gi_01",
        "title": "Hướng dẫn Lâm sàng Tiêu hóa: Đau thượng vị & Trào ngược dạ dày",
        "source": "Phác đồ Điều trị Nội khoa Tiêu hóa - Bộ Y Tế & Hội Tiêu hóa Việt Nam",
        "keywords": ["đau bụng", "dạ dày", "thượng vị", "ợ chua", "trào ngược", "chướng bụng", "đầy hơi", "buồn nôn", "tiêu hóa"],
        "content": (
            "- Nhận diện: Đau âm ỉ hoặc quặn vùng trên rốn (thượng vị), ợ nóng, ợ chua, cồn cào khi đói hoặc đau tăng sau ăn đồ chua cay.\n"
            "- Xử trí tại nhà & Dinh dưỡng tạm thời: Uống nước ấm từng ngụm nhỏ, ăn thức ăn mềm, dễ tiêu (cháo loãng, bánh mì, yến mạch). Tuyệt đối tránh nước chanh, cam, cà phê, trà đặc, ớt, tiêu và thực phẩm chiên xào nhiều dầu mỡ.\n"
            "- Lưu ý vận động: Tránh nằm ngay sau khi ăn ít nhất 2 giờ; tạm dừng các bài tập gập bụng (sit-ups, crunches) hoặc nâng tạ nặng vì làm tăng áp lực ổ bụng.\n"
            "- Dấu hiệu nguy hiểm (Red Flags): Đau bụng dữ dội như dao đâm, nôn ra máu, đi ngoài phân đen như bã cà phê, sốt cao kèm cứng bụng."
        )
    },
    {
        "id": "med_metabolic_01",
        "title": "Hướng dẫn Lâm sàng: Hạ đường huyết cơ năng & Tụt huyết áp tư thế",
        "source": "Hướng dẫn Chẩn đoán và Điều trị Rối loạn Chuyển hóa - Viện Dinh Dưỡng Quốc gia",
        "keywords": ["chóng mặt", "choáng váng", "hoa mắt", "hạ đường huyết", "tụt huyết áp", "mệt mỏi", "run tay", "vã mồ hôi", "xây xẩm"],
        "content": (
            "- Nhận diện: Cảm giác đầu óc quay cuồng, choáng váng khi đứng lên đột ngột, hoa mắt, run tay, tim đập nhanh, vã mồ hôi lạnh, đói lả.\n"
            "- Xử trí tại nhà: Lập tức ngồi hoặc nằm nghỉ ở nơi thoáng mát, kê cao chân nhẹ để dồn máu về não và tim. Nếu nghi ngờ hạ đường huyết (đã lâu chưa ăn), ngậm 1 viên kẹo ngọt hoặc uống 100-150ml nước đường/nước trái cây ấm loãng (nếu không có chống chỉ định dạ dày).\n"
            "- Khuyến nghị thể trạng: Chuyển cường độ bài tập sang mức 'Light' (vận động nhẹ, phục hồi), không tập khi bụng đói hoặc đang mệt mỏi.\n"
            "- Dấu hiệu nguy hiểm (Red Flags): Mất ý thức, ngất xỉu, co giật, lú lẫn, yếu liệt một bên cơ thể, nói khó."
        )
    },
    {
        "id": "med_allergy_01",
        "title": "Hướng dẫn Lâm sàng: Dị ứng thực phẩm & Hội chứng không dung nạp",
        "source": "Hướng dẫn Lâm sàng Miễn dịch Dị ứng - Hội Dị ứng Miễn dịch Lâm sàng",
        "keywords": ["dị ứng", "dị ứng sữa", "lactose", "dị ứng hải sản", "tôm cua", "đậu phộng", "đậu nành", "mẩn ngứa", "mề đay", "phù môi"],
        "content": (
            "- Nhận diện: Ngứa rát cổ họng, nổi mẩn đỏ, mề đay, sưng mí mắt/môi, đau bụng hoặc tiêu chảy ngay sau khi ăn thực phẩm lạ.\n"
            "- Ràng buộc cứng: Loại trừ tuyệt đối 100% thực phẩm gây dị ứng khỏi khẩu phần (đặc biệt là 3 nhóm chính: đậu/đậu phộng, hải sản tôm cua, sữa chứa lactose).\n"
            "- Xử trí tạm thời: Uống nhiều nước lọc để thanh lọc, tránh cào gãi làm tổn thương da.\n"
            "- Dấu hiệu nguy hiểm (Red Flags - Phản vệ độ II trở lên): Khó thở, thở rít thanh quản, nghẹn họng, tụt huyết áp, sưng phù toàn bộ mặt -> Cần tiêm Adrenaline và đưa đi cấp cứu ngay."
        )
    },
    {
        "id": "med_sports_01",
        "title": "Phác đồ Y học Thể thao: Đau cơ sau tập (DOMS) & Viêm khớp",
        "source": "Cẩm nang Y học Thể thao & Phục hồi Chức năng Thể chất",
        "keywords": ["đau cơ", "nhức mỏi", "chuột rút", "căng cơ", "đau khớp", "khớp gối", "cổ chân", "tập gym", "doms", "thoái hóa"],
        "content": (
            "- Nhận diện: Đau nhức cơ bắp ê ẩm xuất hiện sau tập 12-48 giờ (DOMS). Nếu đau nhói đột ngột khi vận động thì có nguy cơ căng cơ hoặc tổn thương dây chằng.\n"
            "- Xử trí tại nhà: Áp dụng nguyên tắc RICE nếu đau cấp tính (Nghỉ ngơi, Chườm lạnh 15-20 phút, Băng ép nhẹ, Kê cao chi). Nếu chỉ là đau mỏi ê ẩm cơ (DOMS), tắm nước ấm, giãn cơ thụ động nhẹ nhàng, bổ sung đầy đủ nước và khoáng chất Magie, Kali.\n"
            "- Điều chỉnh thể lực: Giảm mức độ vận động về 'Light', tránh tập nặng lại nhóm cơ đang tổn thương cho đến khi hết hẳn cảm giác đau buốt.\n"
            "- Dấu hiệu nguy hiểm (Red Flags): Khớp sưng to đỏ nóng, biến dạng khớp, mất hoàn toàn khả năng chịu lực, nước tiểu có màu sẫm như xì dầu (nghi ngờ tiêu cơ vân)."
        )
    },
    {
        "id": "med_cardio_01",
        "title": "Hướng dẫn Tim mạch & Huyết áp trong Thể thao",
        "source": "Khuyến cáo Vận động Thể lực cho Người Tăng Huyết áp & Tim mạch - Hội Tim mạch Việt Nam",
        "keywords": ["tim đập nhanh", "hồi hộp", "khó thở", "huyết áp", "tăng huyết áp", "đau ngực", "nặng ngực", "nhịp tim"],
        "content": (
            "- Nhận diện: Cảm giác tim đập dồn dập, hồi hộp trong ngực, khó thở nhẹ khi gắng sức.\n"
            "- Xử trí an toàn: Giảm dần tốc độ (cool-down), ngồi nghỉ ngơi thả lỏng, hít thở sâu bằng mũi và thở ra chậm bằng miệng.\n"
            "- Nguyên tắc cá nhân hóa: Người có chỉ số tiền tăng huyết áp hoặc huyết áp cao bắt buộc tuân thủ chế độ ăn giảm muối (dưới 5g muối/ngày), giảm mỡ động vật, không tập các bài nâng tạ nín thở (Valsalva maneuver).\n"
            "- Dấu hiệu nguy hiểm (Red Flags): Cơn đau thắt ngực kiểu đè nặng bóp nghẹt kéo dài trên 5 phút, lan lên cổ, hàm hoặc xuống cánh tay trái, vã mồ hôi hột, khó thở dữ dội."
        )
    },
    {
        "id": "med_general_safety",
        "title": "Quy chuẩn An toàn Chăm sóc Sức khỏe Ban đầu FitBreak",
        "source": "Tiêu chuẩn An toàn Y tế Dự phòng & Chăm sóc Thể chất Học đường",
        "keywords": ["sức khỏe", "thể trạng", "bmi", "chế độ ăn", "nghỉ ngơi", "thể lực", "bổ sung"],
        "content": (
            "- Nguyên tắc an toàn y học thể thao: Lắng nghe cơ thể, khởi động kỹ trước vận động và hạ nhiệt sau bài tập.\n"
            "- Cân bằng năng lượng & vi chất: Duy trì thâm hụt calo nhẹ nhàng nếu cần giảm cân; chia nhỏ bữa ăn nếu dễ bị đầy bụng hoặc hạ đường huyết; uống đủ nước (tối thiểu 0.4 lít / 10kg cân nặng mỗi ngày).\n"
            "- Đảm bảo giấc ngủ từ 7-8 tiếng để phục hồi hệ thần kinh và cơ xương khớp."
        )
    }
]

def retrieve_medical_docs(user_message: str, top_k: int = 2) -> str:
    """
    RAG Retrieval: Tìm kiếm các đoạn tài liệu y khoa chuẩn xác dựa trên triệu chứng của người dùng.
    """
    if not user_message:
        return CLINICAL_KNOWLEDGE_BASE[-1]["content"]

    clean_msg = user_message.lower()
    scored_docs = []

    for doc in CLINICAL_KNOWLEDGE_BASE:
        score = 0
        for kw in doc["keywords"]:
            if kw in clean_msg:
                score += 2
        # Tăng điểm nếu từ khóa xuất hiện nhiều
        words = set(re.findall(r"\w+", clean_msg))
        for w in words:
            if len(w) >= 3 and w in doc["content"].lower():
                score += 0.5
        scored_docs.append((score, doc))

    scored_docs.sort(key=lambda x: x[0], reverse=True)

    # Chọn top_k tài liệu có điểm số cao nhất (hoặc mặc định nếu điểm = 0)
    selected = [doc for score, doc in scored_docs[:top_k] if score > 0]
    if not selected:
        selected = [CLINICAL_KNOWLEDGE_BASE[0], CLINICAL_KNOWLEDGE_BASE[1]]

    formatted_docs = []
    for i, doc in enumerate(selected, 1):
        formatted_docs.append(
            f"--- TRÍCH ĐOẠN {i} [{doc['title']}] ---\n"
            f"Nguồn: {doc['source']}\n"
            f"{doc['content']}"
        )

    return "\n\n".join(formatted_docs)
