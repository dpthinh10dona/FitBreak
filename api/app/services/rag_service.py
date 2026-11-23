# IMPORT & CALL FUNCTION #
import json, re, asyncio
from pathlib import Path
from typing import Optional
import pandas as pd
from pydantic import BaseModel, Field

from app.core.exceptions import (
    InvalidResponseError,
    InvalidUserInformationError,
    NoMatchingFoodsError,
)
from app.core.ollama_client import generate_chat
from app.services.prompt_builder import prompt_builder
from app.services.safety_guardrail import check_filtered_meals_sufficiency
#####

# DATABASE #
DATA_PATH = Path(__file__).resolve().parents[1] / "core" / "dataset" / "Vietnamese_Food_Database.csv"
DF_FOODS = pd.read_csv(DATA_PATH)
DF_FOODS["allergens"] = DF_FOODS["allergens"].fillna("")

# Dùng cơm trắng 100g làm chuẩn tính toán calo/protein/giá
RICE_NUTRIENTS_PER_100G = {
      "calories": 130,
      "protein": 2.7,
      "carbs": 28,
      "fat": 0.3,
      "price": 2000,
}


def get_user_value(user_information: dict, field: str, default=None):
      if isinstance(user_information, dict):
            return user_information.get(field, default)
      return getattr(user_information, field, default)


ALLERGEN_SYNONYMS = {
    'đậu nành': 'soy',
    'dau nanh': 'soy',
    'soy': 'soy',
    'lactose': 'lactose',
    'sữa': 'lactose',
    'sua': 'lactose',
    'hải sản': 'seafood',
    'hai san': 'seafood',
    'seafood': 'seafood',
    'trứng': 'egg',
    'trung': 'egg',
    'egg': 'egg',
    'đậu phộng': 'peanut',
    'dau phong': 'peanut',
    'peanut': 'peanut',
}

DIET_SYNONYMS = {
    'ăn chay': 'vegetarian',
    'anchay': 'vegetarian',
    'vegetarian': 'vegetarian',
    'eat clean': 'eatclean',
    'eatclean': 'eatclean',
    'eat_clean': 'eatclean',
    'không kiêng': '',
    'khong kieng': '',
    'khongkieng': '',
    'home_cooked': 'home_cooked',
    'homecooked': 'home_cooked',
    'none': '',
    'all': '',
}


def _normalize_diet_key(value) -> str:
    raw = str(value).strip().lower()
    return DIET_SYNONYMS.get(raw, re.sub(r'[\s_\-]+', '', raw))


def filter_foods(df: pd.DataFrame, user_diet: str, user_allergens) -> pd.DataFrame:
      if isinstance(user_allergens, str):
            raw_allergens = [
                  a.strip().lower() for a in user_allergens.replace(',', ';').split(';') if a.strip()
            ]
      else:
            raw_allergens = [
                  a.strip().lower() for a in (user_allergens or []) if a and a.strip()
            ]

      mapped_allergens = set()
      for a in raw_allergens:
            if a in ('đậu', 'dau', 'beans', 'legumes'):
                  mapped_allergens.add('soy')
                  mapped_allergens.add('peanut')
            else:
                  mapped_allergens.add(ALLERGEN_SYNONYMS.get(a, a))

      def has_allergen(item_allergens):
            if not item_allergens:
                  return False
            item_list = [a.strip().lower() for a in str(item_allergens).split(';')]
            return any(a in mapped_allergens for a in item_list)

      # 1. Lọc dị ứng
      valid_df = df[~df['allergens'].apply(has_allergen)].copy()

      # 2. Lọc chế độ ăn
      norm_user_diet = _normalize_diet_key(user_diet)
      if norm_user_diet and norm_user_diet != 'home_cooked':
        valid_df = valid_df[
            valid_df['diet_type'].apply(
                lambda diets: norm_user_diet in {
                    _normalize_diet_key(d) for d in str(diets).split(';')
                }
            )
        ]

      return valid_df


import unicodedata

def normalize_text(text: str) -> str:
      return unicodedata.normalize("NFC", str(text).strip().lower())

def scale_ingredients_text(ingredients_str: str, multiplier: float) -> str:
      """Nhân khối lượng/thành phần món ăn theo hệ số portion_multiplier."""
      if abs(multiplier - 1.0) < 0.05 or not ingredients_str:
            return ingredients_str

      def repl(match):
            prefix = match.group(1)
            num_str = match.group(2)
            unit = match.group(3)
            try:
                  val = float(num_str)
                  scaled = val * multiplier
                  scaled_str = f"{scaled:.0f}" if scaled >= 10 else f"{scaled:.1f}"
                  if scaled_str.endswith(".0"):
                        scaled_str = scaled_str[:-2]
                  return f"{prefix}{scaled_str}{unit}"
            except Exception:
                  return match.group(0)

      return re.sub(r'([-\s:]+)(\d+(?:\.\d+)?)\s*([a-zA-Zà-ỹÀ-Ỹ%]+)', repl, ingredients_str)

def get_dish_info(dish_name: str, df: pd.DataFrame) -> dict:
      """Helper tra cứu thông tin dinh dưỡng an toàn từ tên món."""
      norm_target = normalize_text(dish_name)

      matched = df[df["name"].apply(normalize_text) == norm_target]

      if not matched.empty:
            row = matched.iloc[0]
            ingredients_val = row.get("ingredients", row["name"])
            limitation_val = row.get("limitation_type", "")
            citation_val = row.get("source_citation", "")
            period_val = row.get("valid_period", "")
            return {
                  "calories": float(row.get("calories", 0)),
                  "protein": float(row.get("protein_g", 0)),
                  "carbs": float(row.get("carbs_g", 0)),
                  "fat": float(row.get("fat_g", 0)),
                  "price": float(row.get("cost_vnd", 0)),
                  "ingredients": str(ingredients_val) if pd.notna(ingredients_val) else row["name"],
                  "limitation_type": str(limitation_val).strip() if pd.notna(limitation_val) else "",
                  "source_citation": str(citation_val).strip() if pd.notna(citation_val) else "",
                  "valid_period": str(period_val).strip() if pd.notna(period_val) else "",
                  "real_name": row["name"]
            }
      raise InvalidResponseError(f"Món ăn không có trong database: {dish_name}")
#####

# PARSE DISH #
class Breakfast(BaseModel):
      dish_name: str
      portion_multiplier: float = Field(default=1.0, ge=0.5, le=3.0, description="Hệ số khẩu phần món ăn (VD: 1.0, 1.2, 1.5)")

class MainMeal(BaseModel):
      dish_name: Optional[str] = None
      main_dish: Optional[str] = None
      portion_multiplier: float = Field(default=1.0, ge=0.5, le=3.0, description="Hệ số khẩu phần món ăn (VD: 1.0, 1.2, 1.5)")
      rice_grams: int = Field(default=0, ge=0, le=300, description="Số gram cơm (tối đa 300g)")

      @property
      def target_dish_name(self) -> str:
            return self.dish_name or self.main_dish or ""

class MealsPlan(BaseModel):
      breakfast: Breakfast
      lunch: MainMeal
      dinner: MainMeal

class LLMMealResponse(BaseModel):
      estimated_total_cost: Optional[float] = 0
      nutrition_note: Optional[str] = Field(default="", description="Lưu ý/giải thích ngắn gọn về lý do chọn thực đơn này")
      meals: MealsPlan


def parse_llm_meal_response(raw_text: str) -> LLMMealResponse:
      match = re.search(r"\{[\s\S]*\}", raw_text)
      if not match:
            raise InvalidResponseError("LLM không trả về JSON hợp lệ")
      try:
            data = json.loads(match.group(0))
            return LLMMealResponse(**data)
      except Exception as e:
            raise InvalidResponseError(f"Không thể parse JSON từ LLM: {str(e)}")


def validate_user_information(user_information: dict) -> None:
      required_fields = ("calories_need", "daily_budget", "protein_need", "aim", "diet_type")
      missing_fields = [
            field for field in required_fields if get_user_value(user_information, field) is None
      ]
      if missing_fields:
            raise InvalidUserInformationError(
                  f"Thiếu thông tin người dùng: {', '.join(missing_fields)}"
            )

      numeric_fields = ("calories_need", "daily_budget", "protein_need")
      for field in numeric_fields:
            value = get_user_value(user_information, field)
            if not isinstance(value, (int, float)) or value < 0:
                  raise InvalidUserInformationError(f"{field} phải là số không âm")


def format_meal_summary(response: str, df_pool: pd.DataFrame, user_information: dict) -> dict:
      meal_plan = parse_llm_meal_response(response)

      # 1. Lấy thông tin món gốc
      bf = meal_plan.meals.breakfast
      bf_info = get_dish_info(bf.dish_name, df_pool)
      bf_mult = max(0.5, min(float(getattr(bf, "portion_multiplier", 1.0) or 1.0), 3.0))

      lu = meal_plan.meals.lunch
      lu_main = get_dish_info(getattr(lu, "target_dish_name", lu.main_dish), df_pool)
      lu_mult = max(0.5, min(float(getattr(lu, "portion_multiplier", 1.0) or 1.0), 3.0))
      lu_rice_grams = getattr(lu, "rice_grams", 0) or 0

      dn = meal_plan.meals.dinner
      dn_main = get_dish_info(getattr(dn, "target_dish_name", dn.main_dish), df_pool)
      dn_mult = max(0.5, min(float(getattr(dn, "portion_multiplier", 1.0) or 1.0), 3.0))
      dn_rice_grams = getattr(dn, "rice_grams", 0) or 0

      # HẬU KIỂM & TỰ ĐỘNG CÂN ĐỐI CẢ NGÂN SÁCH VÀ NĂNG LƯỢNG TDEE (POST-CHECK DUAL OPTIMIZER)
      daily_budget = float(get_user_value(user_information, "daily_budget", 0))
      target_calories = float(get_user_value(user_information, "calories_need", 0))

      def calc_cost(b_m, l_m, d_m, l_r, d_r):
            return (
                  bf_info["price"] * b_m
                  + lu_main["price"] * l_m + (l_r / 100) * RICE_NUTRIENTS_PER_100G["price"]
                  + dn_main["price"] * d_m + (d_r / 100) * RICE_NUTRIENTS_PER_100G["price"]
            )

      def calc_calories(b_m, l_m, d_m, l_r, d_r):
            return (
                  bf_info["calories"] * b_m
                  + lu_main["calories"] * l_m + (l_r / 100) * RICE_NUTRIENTS_PER_100G["calories"]
                  + dn_main["calories"] * d_m + (d_r / 100) * RICE_NUTRIENTS_PER_100G["calories"]
            )

      initial_cost = calc_cost(bf_mult, lu_mult, dn_mult, lu_rice_grams, dn_rice_grams)

      # 1. Nếu chi phí vượt ngân sách cho phép -> hạ dần portion_multiplier
      if daily_budget > 0 and initial_cost > daily_budget:
            for _ in range(25):
                  curr_cost = calc_cost(bf_mult, lu_mult, dn_mult, lu_rice_grams, dn_rice_grams)
                  if curr_cost <= daily_budget:
                        break
                  max_mult = max(bf_mult, lu_mult, dn_mult)
                  if max_mult > 1.0:
                        if bf_mult == max_mult:
                              bf_mult = round(max(1.0, bf_mult - 0.05), 2)
                        elif lu_mult == max_mult:
                              lu_mult = round(max(1.0, lu_mult - 0.05), 2)
                        else:
                              dn_mult = round(max(1.0, dn_mult - 0.05), 2)
                  else:
                        if lu_mult >= dn_mult and lu_mult > 0.8:
                              lu_mult = round(lu_mult - 0.05, 2)
                        elif dn_mult > 0.8:
                              dn_mult = round(dn_mult - 0.05, 2)
                        elif bf_mult > 0.8:
                              bf_mult = round(bf_mult - 0.05, 2)
                        else:
                              break

      # 2. KIỂM SOÁT THIẾU HỤT CALO (CALORIE DEFICIT OPTIMIZATION):
      # Nếu calo sau khi tính toán vẫn bị hụt so với TDEE (dưới 88% TDEE) và ngân sách vẫn còn dư:
      if target_calories > 0:
            curr_cals = calc_calories(bf_mult, lu_mult, dn_mult, lu_rice_grams, dn_rice_grams)
            curr_cost = calc_cost(bf_mult, lu_mult, dn_mult, lu_rice_grams, dn_rice_grams)

            # A. Nếu món sáng có calo quá thấp (< 350 kcal, vd Bánh mỳ 178 kcal) và ngân sách còn rộng
            if bf_info["calories"] * bf_mult < 350 and bf_mult < 1.8:
                  cost_step = bf_info["price"] * 0.25
                  if curr_cost + cost_step <= daily_budget:
                        bf_mult = round(bf_mult + 0.3, 2)
                        curr_cals = calc_calories(bf_mult, lu_mult, dn_mult, lu_rice_grams, dn_rice_grams)
                        curr_cost = calc_cost(bf_mult, lu_mult, dn_mult, lu_rice_grams, dn_rice_grams)

            # B. Bù calo sạch bằng cơm trắng (chỉ 2,000đ/100g = 130 kcal)
            for _ in range(10):
                  curr_cals = calc_calories(bf_mult, lu_mult, dn_mult, lu_rice_grams, dn_rice_grams)
                  curr_cost = calc_cost(bf_mult, lu_mult, dn_mult, lu_rice_grams, dn_rice_grams)
                  if curr_cals >= target_calories * 0.90:
                        break
                  # Kiểm tra còn đủ 1,000đ để thêm 50g cơm không (50g = 65 kcal)
                  if curr_cost + 1000 <= daily_budget:
                        if dn_rice_grams <= lu_rice_grams and dn_rice_grams <= 250:
                              dn_rice_grams += 50
                        elif lu_rice_grams <= 250:
                              lu_rice_grams += 50
                        else:
                              break
                  else:
                        break

      # 2. Tính toán vi chất dinh dưỡng cuối cùng cho từng bữa
      # Bữa sáng
      bf_cal = bf_info["calories"] * bf_mult
      bf_pro = bf_info["protein"] * bf_mult
      bf_carb = bf_info["carbs"] * bf_mult
      bf_fat = bf_info["fat"] * bf_mult
      bf_cost = bf_info["price"] * bf_mult

      bf_name_display = bf_info["real_name"]
      if abs(bf_mult - 1.0) >= 0.05:
            bf_name_display = f'{bf_info["real_name"]} (x{bf_mult:.1f} phần)'

      # Bữa trưa
      lu_dish_cal = lu_main["calories"] * lu_mult
      lu_dish_pro = lu_main["protein"] * lu_mult
      lu_dish_carb = lu_main["carbs"] * lu_mult
      lu_dish_fat = lu_main["fat"] * lu_mult
      lu_dish_cost = lu_main["price"] * lu_mult

      lu_rice_cal = (lu_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["calories"]
      lu_rice_pro = (lu_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["protein"]
      lu_rice_carb = (lu_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["carbs"]
      lu_rice_fat = (lu_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["fat"]
      lu_rice_cost = (lu_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["price"]

      lu_total_cal = lu_dish_cal + lu_rice_cal
      lu_total_pro = lu_dish_pro + lu_rice_pro
      lu_total_carb = lu_dish_carb + lu_rice_carb
      lu_total_fat = lu_dish_fat + lu_rice_fat
      lu_total_cost = lu_dish_cost + lu_rice_cost

      lu_name_display = lu_main["real_name"]
      if abs(lu_mult - 1.0) >= 0.05:
            lu_name_display = f'{lu_main["real_name"]} (x{lu_mult:.1f} phần)'
      if lu_rice_grams > 0:
            lu_name_display += f' + {lu_rice_grams}g cơm'

      # Bữa tối
      dn_dish_cal = dn_main["calories"] * dn_mult
      dn_dish_pro = dn_main["protein"] * dn_mult
      dn_dish_carb = dn_main["carbs"] * dn_mult
      dn_dish_fat = dn_main["fat"] * dn_mult
      dn_dish_cost = dn_main["price"] * dn_mult

      dn_rice_cal = (dn_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["calories"]
      dn_rice_pro = (dn_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["protein"]
      dn_rice_carb = (dn_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["carbs"]
      dn_rice_fat = (dn_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["fat"]
      dn_rice_cost = (dn_rice_grams / 100) * RICE_NUTRIENTS_PER_100G["price"]

      dn_total_cal = dn_dish_cal + dn_rice_cal
      dn_total_pro = dn_dish_pro + dn_rice_pro
      dn_total_carb = dn_dish_carb + dn_rice_carb
      dn_total_fat = dn_dish_fat + dn_rice_fat
      dn_total_cost = dn_dish_cost + dn_rice_cost

      dn_name_display = dn_main["real_name"]
      if abs(dn_mult - 1.0) >= 0.05:
            dn_name_display = f'{dn_main["real_name"]} (x{dn_mult:.1f} phần)'
      if dn_rice_grams > 0:
            dn_name_display += f' + {dn_rice_grams}g cơm'

      # Tổng kết
      total_cal = bf_cal + lu_total_cal + dn_total_cal
      total_pro = bf_pro + lu_total_pro + dn_total_pro
      total_carb = bf_carb + lu_total_carb + dn_total_carb
      total_fat = bf_fat + lu_total_fat + dn_total_fat
      total_cost = bf_cost + lu_total_cost + dn_total_cost

      nutrition_note = getattr(meal_plan, "nutrition_note", "") or ""

      # Thu thập các điều kiện hạn chế/chú ý y tế từ các món ăn được chọn
      raw_limitations = []
      for info in [bf_info, lu_main, dn_main]:
            lim = info.get("limitation_type", "").strip()
            if lim and lim not in raw_limitations:
                  raw_limitations.append(lim)

      return {
            "total_calories": round(total_cal),
            "total_protein": round(total_pro, 1),
            "total_carbs": round(total_carb, 1),
            "total_fat": round(total_fat, 1),
            "total_cost": round(total_cost),
            "nutrition_note": nutrition_note.strip(),
            "limitation_notes": raw_limitations,
            "meals": [
                  {
                        "type": "Bữa sáng",
                        "time": "07:00",
                        "name": bf_name_display,
                        "desc": f"Khẩu phần: x{bf_mult:.1f}" if abs(bf_mult - 1.0) >= 0.05 else "Khẩu phần chuẩn",
                        "portion_multiplier": round(bf_mult, 2),
                        "kcal": round(bf_cal),
                        "cost": round(bf_cost),
                        "protein": round(bf_pro, 1),
                        "carbs": round(bf_carb, 1),
                        "fat": round(bf_fat, 1),
                        "ingredients": scale_ingredients_text(bf_info["ingredients"], bf_mult),
                        "limitation_type": bf_info.get("limitation_type", ""),
                        "source_citation": bf_info.get("source_citation", ""),
                        "valid_period": bf_info.get("valid_period", ""),
                        "source_verification_status": "UNVERIFIED_ROW",
                  },
                  {
                        "type": "Bữa trưa",
                        "time": "12:00",
                        "name": lu_name_display,
                        "desc": f"Món chính x{lu_mult:.1f} + {lu_rice_grams}g cơm" if lu_rice_grams > 0 else f"Khẩu phần: x{lu_mult:.1f}",
                        "portion_multiplier": round(lu_mult, 2),
                        "rice_grams": lu_rice_grams,
                        "kcal": round(lu_total_cal),
                        "cost": round(lu_total_cost),
                        "protein": round(lu_total_pro, 1),
                        "carbs": round(lu_total_carb, 1),
                        "fat": round(lu_total_fat, 1),
                        "ingredients": scale_ingredients_text(lu_main["ingredients"], lu_mult),
                        "limitation_type": lu_main.get("limitation_type", ""),
                        "source_citation": lu_main.get("source_citation", ""),
                        "valid_period": lu_main.get("valid_period", ""),
                        "source_verification_status": "UNVERIFIED_ROW",
                  },
                  {
                        "type": "Bữa tối",
                        "time": "19:00",
                        "name": dn_name_display,
                        "desc": f"Món chính x{dn_mult:.1f} + {dn_rice_grams}g cơm" if dn_rice_grams > 0 else f"Khẩu phần: x{dn_mult:.1f}",
                        "portion_multiplier": round(dn_mult, 2),
                        "rice_grams": dn_rice_grams,
                        "kcal": round(dn_total_cal),
                        "cost": round(dn_total_cost),
                        "protein": round(dn_total_pro, 1),
                        "carbs": round(dn_total_carb, 1),
                        "fat": round(dn_total_fat, 1),
                        "ingredients": scale_ingredients_text(dn_main["ingredients"], dn_mult),
                        "limitation_type": dn_main.get("limitation_type", ""),
                        "source_citation": dn_main.get("source_citation", ""),
                        "valid_period": dn_main.get("valid_period", ""),
                        "source_verification_status": "UNVERIFIED_ROW",
                  },
            ],
      }

# MAIN RAG #
async def process_rag_pipeline(user_information: dict) -> str:
      validate_user_information(user_information)

      diet_type = get_user_value(user_information, "diet_type")
      allergen = get_user_value(user_information, "allergen", "")

      # Retrieval: Lọc danh sách món hợp lệ từ CSV
      filtered_df = filter_foods(DF_FOODS, diet_type, allergen)
      if filtered_df.empty:
            raise NoMatchingFoodsError("Không tìm thấy món ăn phù hợp với chế độ ăn và dị ứng.")

      # Neu co danh sach mon cu can doi (exclude_dishes), loai bo chung neu con du mon khac
      exclude_dishes = get_user_value(user_information, 'exclude_dishes', [])
      if exclude_dishes and isinstance(exclude_dishes, list):
            norm_excludes = {normalize_text(d) for d in exclude_dishes if d}
            remaining_df = filtered_df[~filtered_df['name'].apply(lambda n: normalize_text(n) in norm_excludes)]
            if len(remaining_df) >= 3:
                  filtered_df = remaining_df

      # Post-retrieval guardrail: không gọi LLM nếu kho món sau lọc không đủ
      # số lượng, ngân sách hoặc khả năng đáp ứng năng lượng mục tiêu.
      sufficiency = check_filtered_meals_sufficiency(
            filtered_df=filtered_df,
            target_calories=float(get_user_value(user_information, "calories_need", 0)),
            daily_budget_vnd=float(get_user_value(user_information, "daily_budget", 0)),
      )
      if not sufficiency.allow_ai_generation:
            blocked = sufficiency.model_dump()
            return {"guardrail": blocked, **blocked}

      # Truyền filtered_df vào prompt_builder để LLM chỉ chọn trong danh sách này
      food_rec = get_user_value(user_information, "food_recommendation", None)

      prompt = await prompt_builder(
            calories_need=get_user_value(user_information, "calories_need"),
            daily_budget=get_user_value(user_information, "daily_budget"),
            protein_need=get_user_value(user_information, "protein_need"),
            aim=get_user_value(user_information, "aim"),
            diet_type=diet_type,
            allergen=allergen,
            filtered_food=filtered_df,
            food_recommendation=food_rec,
      )

      response = await generate_chat(prompt, response_format=LLMMealResponse.model_json_schema())
      return format_meal_summary(response, filtered_df, user_information)

async def main():
      user_information = {
            "calories_need": 2000,
            "protein_need": 110,
            "daily_budget": 120000,
            "aim": "Tăng cơ",
            "diet_type": "home_cooked",
            "allergen": "seafood"
      }

      result = await process_rag_pipeline(user_information)
      print(result)

if __name__ == "__main__":
      asyncio.run(main())
