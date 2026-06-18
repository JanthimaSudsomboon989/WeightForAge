"""
ประเมินน้ำหนักอายุ 0-72 เดือน
คลินิกสุขภาพเด็กดี(WBC) โรงพยาบาลพรหมคีรี
บันทึกข้อมูลลง Google Sheet
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials


# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ประเมินน้ำหนักอายุ 0-72 เดือน | รพ.พรหมคีรี",
    page_icon="📊",
    layout="centered",
)


# ─── Google Sheet config ──────────────────────────────────────────────────────
SPREADSHEET_ID = "1jWOmpP0W40lADwGgwaYbD5PBxf0aZkPOfAf_Yq7m8wo"
WORKSHEET_NAME = "Sheet1"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_COLUMNS = [
    "timestamp",
    "sex",
    "child_id",
    "child_name",
    "guardian",
    "vhv",
    "guardian_tel",
    "vhv_tel",
    "house_no",
    "moo",
    "municipality",
    "height_cm",
    "head_cm",
    "development",
    "milk1",
    "milk2",
    "age_total_months",
    "weight_kg",
    "result",
    "category",
]


@st.cache_resource
def get_google_sheet():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.sheet1

    return worksheet


def setup_sheet_header():
    worksheet = get_google_sheet()
    values = worksheet.get_all_values()

    if not values:
        worksheet.append_row(SHEET_COLUMNS, value_input_option="RAW")
        return

    current_header = values[0]

    if current_header != SHEET_COLUMNS:
        worksheet.update("A1:T1", [SHEET_COLUMNS])


def load_records():
    try:
        setup_sheet_header()
        worksheet = get_google_sheet()
        records = worksheet.get_all_records()
        return records
    except Exception as e:
        st.error(f"เชื่อมต่อ Google Sheet ไม่สำเร็จ: {e}")
        return []


def save_record(record: dict):
    setup_sheet_header()
    worksheet = get_google_sheet()

    row = [str(record.get(col, "")) for col in SHEET_COLUMNS]

    # ใช้ RAW เพื่อกันเลขบัตร/เบอร์โทรโดนแปลงเป็นตัวเลข
    worksheet.append_row(row, value_input_option="RAW")


def delete_record(index: int):
    setup_sheet_header()
    worksheet = get_google_sheet()

    # index เริ่มจาก 0 แต่ Google Sheet แถว 1 คือ header
    row_number = index + 2

    if row_number >= 2:
        worksheet.delete_rows(row_number)


# ─── WHO Weight-for-Age reference tables ──────────────────────────────────────
# Values: (SD3neg, SD2neg, median, SD2pos, SD3pos) in kg
WHO_BOYS = {
    0: (2.1, 2.9, 3.3, 4.4, 5.0),
    1: (2.9, 3.9, 4.5, 5.8, 6.6),
    2: (3.8, 4.9, 5.6, 7.1, 8.0),
    3: (4.4, 5.7, 6.4, 8.0, 9.0),
    4: (4.9, 6.2, 7.0, 8.7, 9.7),
    5: (5.3, 6.7, 7.5, 9.3, 10.4),
    6: (5.7, 7.1, 7.9, 9.8, 10.9),
    7: (6.0, 7.4, 8.3, 10.3, 11.4),
    8: (6.3, 7.7, 8.6, 10.7, 11.9),
    9: (6.6, 8.2, 9.2, 11.3, 12.7),
    10: (6.8, 8.4, 9.4, 11.7, 13.0),
    11: (7.0, 8.6, 9.7, 12.0, 13.3),
    12: (7.1, 8.9, 9.9, 12.3, 13.8),
    15: (7.6, 9.5, 10.7, 13.3, 14.9),
    18: (8.1, 10.0, 11.3, 13.9, 15.7),
    21: (8.6, 10.5, 11.8, 14.7, 16.5),
    24: (9.0, 11.0, 12.2, 15.3, 17.1),
    30: (9.8, 11.9, 13.3, 16.9, 19.0),
    36: (10.8, 13.0, 14.3, 18.3, 20.5),
    42: (11.3, 13.7, 15.3, 19.7, 22.2),
    48: (12.1, 14.7, 16.3, 21.2, 23.9),
    54: (12.9, 15.6, 17.5, 22.7, 25.7),
    60: (13.7, 16.8, 18.7, 24.2, 27.4),
    66: (14.5, 17.7, 19.9, 25.9, 29.4),
    72: (15.3, 18.9, 21.2, 27.6, 31.5),
}

WHO_GIRLS = {
    0: (2.0, 2.8, 3.2, 4.2, 4.8),
    1: (2.7, 3.6, 4.2, 5.5, 6.2),
    2: (3.4, 4.5, 5.1, 6.6, 7.5),
    3: (4.0, 5.2, 5.8, 7.5, 8.5),
    4: (4.4, 5.7, 6.4, 8.2, 9.3),
    5: (4.8, 6.1, 6.9, 8.8, 10.0),
    6: (5.1, 6.5, 7.3, 9.3, 10.6),
    7: (5.4, 6.8, 7.6, 9.8, 11.1),
    8: (5.7, 7.0, 8.0, 10.2, 11.6),
    9: (5.8, 7.5, 8.4, 10.9, 12.4),
    10: (6.1, 7.7, 8.7, 11.3, 12.9),
    11: (6.3, 7.9, 9.0, 11.7, 13.4),
    12: (6.3, 8.1, 9.2, 11.9, 13.5),
    15: (6.9, 8.8, 10.0, 13.2, 15.1),
    18: (7.2, 9.2, 10.5, 13.7, 15.5),
    21: (7.6, 9.6, 11.0, 14.5, 16.4),
    24: (8.1, 10.2, 11.5, 14.8, 16.9),
    30: (8.8, 11.1, 12.7, 16.5, 19.0),
    36: (9.6, 12.1, 13.9, 18.1, 20.9),
    42: (10.3, 12.9, 14.8, 19.7, 22.8),
    48: (10.9, 13.7, 15.8, 21.0, 24.5),
    54: (11.7, 14.7, 17.0, 22.7, 26.5),
    60: (12.5, 15.8, 18.3, 24.7, 28.9),
    66: (13.3, 17.0, 19.8, 26.7, 31.5),
    72: (14.1, 17.9, 20.8, 28.5, 33.7),
}


def get_who_ref(sex: str, age_months: int) -> dict:
    table = WHO_BOYS if sex == "ชาย" else WHO_GIRLS
    ages = sorted(table.keys())
    closest = min(ages, key=lambda a: abs(a - age_months))
    v = table[closest]

    return {
        "SD3neg": v[0],
        "SD2neg": v[1],
        "median": v[2],
        "SD2pos": v[3],
        "SD3pos": v[4],
    }


def classify(weight: float, ref: dict) -> tuple:
    if weight < ref["SD3neg"]:
        return "น้ำหนักน้อยกว่าเกณฑ์มาก (< -3 SD)", "#FF9800", "🟠", "very_underweight"

    if weight < ref["SD2neg"]:
        return "น้ำหนักน้อยกว่าเกณฑ์ (-3 SD ถึง -2 SD)", "#FDD835", "🟡", "underweight"

    if weight <= ref["SD2pos"]:
        return "น้ำหนักอยู่ในเกณฑ์ปกติ (-2 SD ถึง +2 SD)", "#00C851", "🟢", "normal"

    if weight <= ref["SD3pos"]:
        return "น้ำหนักมากกว่าเกณฑ์ (+2 SD ถึง +3 SD)", "#FF4B4B", "🔴", "overweight"

    return "น้ำหนักมากกว่าเกณฑ์มาก (> +3 SD)", "#FF4B4B", "🔴", "very_overweight"


# ─── Options ──────────────────────────────────────────────────────────────────
MOO_OPTIONS = ["ม.1", "ม.2", "ม.3", "ม.5", "ม.7", "ม.8"]

MUNICIPALITY_OPTIONS = [
    "เทศบาลตำบลพรหมโลก",
    "เทศบาลตำบลนาเรียง",
    "เทศบาลตำบลอินคีรี",
    "เทศบาลตำบลทอนหงส์",
    "เทศบาลตำบลบ้านเกาะ",
    "อบต.พรหมโลก",
    "อบต.บ้านเกาะ",
    "อบต.อินคีรี",
    "อบต.ทอนหงส์",
    "อบต.นาเรียง",
]


# ─── Session state ────────────────────────────────────────────────────────────
if "show_result" not in st.session_state:
    st.session_state.show_result = False


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.title("📊 ประเมินน้ำหนักอายุ 0-72 เดือน")
st.title("🏥 โรงพยาบาลพรหมคีรี 🏥")


# ── Connection status ─────────────────────────────────────────────────────────
with st.expander("🔌 สถานะการเชื่อมต่อ Google Sheet", expanded=False):
    if st.button("ทดสอบเชื่อมต่อ Google Sheet"):
        try:
            setup_sheet_header()
            ws = get_google_sheet()
            st.success(f"เชื่อมต่อสำเร็จ: {ws.title}")
        except Exception as e:
            st.error(f"เชื่อมต่อไม่สำเร็จ: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# FORM FIELDS
# ═══════════════════════════════════════════════════════════════════════════════

st.header("👥 ข้อมูลเด็ก")
sex = st.selectbox("เพศของเด็ก", ["ชาย", "หญิง"])

st.header("🪪 เลขประจำตัวประชาชน")
child_id = st.text_input(
    "เลขบัตรประชาชน 13 หลัก(ของเด็ก)",
    placeholder="เช่น 1234567890123",
    max_chars=13,
)

if child_id and (not child_id.isdigit() or len(child_id) != 13):
    st.warning("⚠️ กรุณากรอกเลขบัตรประชาชน 13 หลัก (ตัวเลขเท่านั้น)")

st.header("📌 ชื่อ-สกุล")
child_name = st.text_input(
    "ชื่อ-นามสกุลเด็ก",
    placeholder="เช่น กิตติ สมใจดี",
)

guardian_name = st.text_input(
    "ชื่อ-นามสกุลผู้ปกครอง",
    placeholder="เช่น นายพ่อ สมใจดี",
)

vhv_name = st.text_input(
    "ชื่อ-นามสกุล อสม. ที่ดูแล",
    placeholder="เช่น สมหญิง มีเทา",
)

st.header("📞 ข้อมูลติดต่อ")
guardian_phone = st.text_input(
    "เบอร์โทรผู้ปกครอง",
    placeholder="เช่น 0812345678",
    max_chars=10,
)

vhv_phone = st.text_input(
    "เบอร์โทร อสม.",
    placeholder="เช่น 0812345678",
    max_chars=10,
)

house_no = st.text_input("บ้านเลขที่", value="")
moo = st.selectbox("หมู่", MOO_OPTIONS)
municipality = st.selectbox("เทศบาล", MUNICIPALITY_OPTIONS)

st.header("📝 ข้อมูลด้านร่างกายและพฤติกรรม")

col_h, col_hc, col_dev = st.columns(3)

with col_h:
    height_cm = st.number_input(
        "ส่วนสูง (ซม.)",
        min_value=30.0,
        max_value=130.0,
        value=30.0,
        step=0.1,
        format="%.1f",
    )

with col_hc:
    head_cm = st.number_input(
        "รอบศีรษะ (ซม.)",
        min_value=30.0,
        max_value=60.0,
        value=30.0,
        step=0.1,
        format="%.1f",
    )

with col_dev:
    development = st.selectbox(
        "พัฒนาการ",
        ["ปกติ", "สงสัยล่าช้า", "ล่าช้า"],
    )

col_m1, col_m2 = st.columns(2)

with col_m1:
    milk1 = st.selectbox(
        "การกินนม (1)",
        ["นมแม่", "นมผสม"],
    )

with col_m2:
    milk2 = st.selectbox(
        "การกินนม (2)",
        ["ใช้ขวด", "ไม่ใช้ขวด"],
    )

st.header("✏️ ข้อมูลอายุ,น้ำหนัก")

col_y, col_m_age, col_w = st.columns(3)

with col_y:
    age_years = st.number_input(
        "อายุ (ปี)",
        min_value=0,
        max_value=6,
        value=0,
        step=1,
    )

with col_m_age:
    age_months_extra = st.number_input(
        "อายุ (เดือน)",
        min_value=0,
        max_value=11,
        value=0,
        step=1,
    )

with col_w:
    weight_kg = st.number_input(
        "น้ำหนัก (กก.)",
        min_value=0.0,
        max_value=40.0,
        value=0.00,
        step=0.01,
        format="%.2f",
    )

st.header("📨 ยืนยันและบันทึกข้อมูล")
submit = st.button("✅ เสร็จสิ้น", type="secondary")


# ═══════════════════════════════════════════════════════════════════════════════
# SUBMIT LOGIC
# ═══════════════════════════════════════════════════════════════════════════════
if submit:
    errors = []

    if not child_name.strip():
        errors.append("กรุณากรอกชื่อ-นามสกุลเด็ก")

    if not child_id or len(child_id) != 13 or not child_id.isdigit():
        errors.append("กรุณากรอกเลขบัตรประชาชน 13 หลักให้ถูกต้อง")

    if guardian_phone and (not guardian_phone.isdigit() or len(guardian_phone) != 10):
        errors.append("กรุณากรอกเบอร์โทรผู้ปกครอง 10 หลักให้ถูกต้อง")

    if vhv_phone and (not vhv_phone.isdigit() or len(vhv_phone) != 10):
        errors.append("กรุณากรอกเบอร์โทร อสม. 10 หลักให้ถูกต้อง")

    if weight_kg <= 0:
        errors.append("กรุณากรอกน้ำหนักที่ถูกต้อง")

    total_months = age_years * 12 + age_months_extra

    if total_months > 72:
        errors.append("อายุเกิน 72 เดือน กรุณาตรวจสอบ")

    if errors:
        for e in errors:
            st.error(f"❌ {e}")

    else:
        st.session_state.show_result = True

        ref = get_who_ref(sex, total_months)
        label, color, icon, category = classify(weight_kg, ref)

        record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sex": sex,
            "child_id": child_id,
            "child_name": child_name,
            "guardian": guardian_name,
            "vhv": vhv_name,
            "guardian_tel": guardian_phone,
            "vhv_tel": vhv_phone,
            "house_no": house_no,
            "moo": moo,
            "municipality": municipality,
            "height_cm": f"{height_cm:.1f}",
            "head_cm": f"{head_cm:.1f}",
            "development": development,
            "milk1": milk1,
            "milk2": milk2,
            "age_total_months": total_months,
            "weight_kg": f"{weight_kg:.2f}",
            "result": label,
            "category": category,
        }

        try:
            save_record(record)
            st.success("✅ บันทึกข้อมูลลง Google Sheet เรียบร้อยแล้ว")
        except Exception as e:
            st.error(f"❌ บันทึกข้อมูลไม่สำเร็จ: {e}")
            st.stop()

        st.divider()

        st.subheader("📋 ผลการประเมิน")

        c1, c2, c3 = st.columns(3)
        c1.metric("อายุรวม", f"{total_months} เดือน")
        c2.metric("น้ำหนัก", f"{weight_kg:.2f} กก.")
        c3.metric("เกณฑ์มาตรฐาน", f"{ref['median']:.1f} กก.")

        st.markdown(
            f"""
            <div style="
                background:{color}22;
                border-left:6px solid {color};
                padding:16px 20px;
                border-radius:8px;
                margin-top:12px;
            ">
                <h3 style="color:{color};margin:0;">{icon} {label}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### 📊 เกณฑ์อ้างอิง WHO")

        ref_df = pd.DataFrame(
            {
                "ระดับ": [
                    "< -3 SD (น้อยมาก)",
                    "-3 SD",
                    "-2 SD",
                    "✅ มัธยฐาน (ปกติ)",
                    "+2 SD",
                    "+3 SD (มากมาก)",
                ],
                "น้ำหนัก (กก.)": [
                    f"< {ref['SD3neg']:.1f}",
                    f"{ref['SD3neg']:.1f}",
                    f"{ref['SD2neg']:.1f}",
                    f"{ref['median']:.1f}",
                    f"{ref['SD2pos']:.1f}",
                    f"{ref['SD3pos']:.1f}",
                ],
            }
        )

        st.dataframe(ref_df, hide_index=True, use_container_width=True)

        st.markdown("#### 💡 คำแนะนำ")

        if category == "normal":
            st.info(
                "น้ำหนักอยู่ในเกณฑ์ปกติตามมาตรฐาน WHO "
                "ควรติดตามน้ำหนักทุก 1-3 เดือน"
            )

        elif category in ["underweight", "very_underweight"]:
            st.warning(
                "น้ำหนักต่ำกว่าเกณฑ์ ควรประเมินภาวะโภชนาการ "
                "และปรึกษาแพทย์เพื่อวางแผนเสริมสารอาหาร"
            )

        else:
            st.warning(
                "น้ำหนักมากกว่าเกณฑ์ ควรประเมินพฤติกรรมการกินและออกกำลังกาย "
                "และปรึกษาแพทย์เพื่อดูแลสุขภาพระยะยาว"
            )

        if development != "ปกติ":
            st.error(
                f"⚠️ พัฒนาการ: {development} — ควรส่งพบแพทย์เพื่อประเมินเพิ่มเติม"
            )

        st.divider()
        st.subheader("🍽️ ตารางคำแนะนำด้านโภชนาการ")

        NUTRITION_TABLE = [
            {
                "key": "very_underweight",
                "กลุ่ม": "ผอมมาก / น้ำหนักน้อยมาก\n(< -3 SD)",
                "เป้าหมาย": "ฟื้นฟูภาวะโภชนาการเร่งด่วน",
                "คำแนะนำ": (
                    "- อาหารพลังงานหนาแน่น\n"
                    "- เพิ่มมื้ออาหาร 5-6 มื้อ/วัน\n"
                    "- เน้นโปรตีนคุณภาพสูง\n"
                    "- เสริมน้ำมันพืชในอาหาร"
                ),
                "หลักเลี่ยง / เสริม": (
                    "*ควรเสริม Multinutrient,\n"
                    "วิตามิน A, ธาตุเหล็กตามเกณฑ์\n"
                    "และหัตถบำบัด\n"
                    "*หลีกเลี่ยงอาหารไขมันต่ำ"
                ),
                "ตัวอย่างเมนูรายวัน": (
                    "ไข่ตุ๋นผสมหมูบด+ฟักทอง /\n"
                    "แกงจืดเต้าหู้+หมูสับ /\n"
                    "ข้าวบดผสมปลา+ผัก /\n"
                    "โจ๊กไก่+ผัก"
                ),
                "การติดตาม": (
                    "ชั่งน้ำหนักทุก 1 เดือน\n"
                    "ประเมินพฤติกรรมอาหาร\n"
                    "ส่งพบแพทย์/นักโภชนาการ"
                ),
            },
            {
                "key": "underweight",
                "กลุ่ม": "ผอม / น้ำหนักน้อย\n(-3 SD ถึง -2 SD)",
                "เป้าหมาย": "เพิ่มน้ำหนักให้ได้เกณฑ์",
                "คำแนะนำ": (
                    "- อาหารพลังงานหนาแน่น\n"
                    "- เพิ่มมื้ออาหาร 4-5 มื้อ/วัน\n"
                    "- โปรตีนทุกมื้อหลัก\n"
                    "- นมวัวหรือนมแม่ต่อเนื่อง"
                ),
                "หลักเลี่ยง / เสริม": (
                    "*เสริมวิตามิน A และธาตุเหล็ก\n"
                    "*หลีกเลี่ยงน้ำหวาน/ขนมขบเคี้ยว\n"
                    "ที่ให้พลังงานเปล่า"
                ),
                "ตัวอย่างเมนูรายวัน": (
                    "ข้าวสวย+แกงจืด+ไข่ /\n"
                    "ข้าวต้มปลา+ผักต้ม /\n"
                    "กล้วยน้ำว้า+นม /\n"
                    "ผัดผักรวมใส่ไก่"
                ),
                "การติดตาม": (
                    "ชั่งน้ำหนักทุก 1 เดือน\n"
                    "ประเมินพฤติกรรมอาหาร"
                ),
            },
            {
                "key": "normal",
                "กลุ่ม": "น้ำหนักปกติ\n(-2 SD ถึง +2 SD)",
                "เป้าหมาย": "รักษาน้ำหนักให้คงเกณฑ์",
                "คำแนะนำ": (
                    "- อาหารครบ 5 หมู่\n"
                    "- 3 มื้อหลัก + 1-2 ว่าง\n"
                    "- ผักผลไม้หลากสี\n"
                    "- ดื่มน้ำเปล่าเพียงพอ"
                ),
                "หลักเลี่ยง / เสริม": (
                    "*หลีกเลี่ยงน้ำหวาน ขนมหวาน\n"
                    "อาหารแปรรูปโซเดียมสูง\n"
                    "*เสริมวิตามิน D หากอยู่ในร่ม"
                ),
                "ตัวอย่างเมนูรายวัน": (
                    "ข้าว+ผัดผัก+ปลานึ่ง /\n"
                    "ต้มจืดผักรวม+ไก่ /\n"
                    "ผลไม้+นม /\n"
                    "ข้าวกล้อง+ไข่ดาว+ผัก"
                ),
                "การติดตาม": (
                    "ชั่งน้ำหนักทุก 2-3 เดือน\n"
                    "ประเมินพัฒนาการตามวัย"
                ),
            },
            {
                "key": "overweight",
                "กลุ่ม": "อ้วน / น้ำหนักมาก\n(+2 SD ถึง +3 SD)",
                "เป้าหมาย": "ชะลอน้ำหนักไม่ให้เพิ่มเร็ว",
                "คำแนะนำ": (
                    "- ลดน้ำตาล ไขมัน แป้งขัดขาว\n"
                    "- เพิ่มผักใยอาหาร\n"
                    "- ออกกำลังกายเหมาะตามวัย\n"
                    "- ไม่จำกัดอาหารเกินไป"
                ),
                "หลักเลี่ยง / เสริม": (
                    "*หลีกเลี่ยงเครื่องดื่มรสหวาน\n"
                    "ขนมขบเคี้ยว ฟาสต์ฟู้ด\n"
                    "*ไม่แนะนำให้ลดน้ำหนักอย่างเข้มงวด"
                ),
                "ตัวอย่างเมนูรายวัน": (
                    "ข้าวกล้อง+ผัดผัก+ปลา /\n"
                    "ซุปผัก+ไก่ไม่ติดหนัง /\n"
                    "ผลไม้รสหวานน้อย /\n"
                    "นมจืดไขมันต่ำ"
                ),
                "การติดตาม": (
                    "ชั่งน้ำหนักทุก 1 เดือน\n"
                    "ประเมินพฤติกรรมการกิน\n"
                    "และการออกกำลังกาย"
                ),
            },
            {
                "key": "very_overweight",
                "กลุ่ม": "อ้วนมาก / น้ำหนักมากมาก\n(> +3 SD)",
                "เป้าหมาย": "ลดความเสี่ยงภาวะแทรกซ้อน",
                "คำแนะนำ": (
                    "- ปรับพฤติกรรมการกินทั้งครอบครัว\n"
                    "- ลดน้ำตาล ไขมัน อาหารแปรรูป\n"
                    "- เพิ่มกิจกรรมทางกาย\n"
                    "- ติดตามสม่ำเสมอ"
                ),
                "หลักเลี่ยง / เสริม": (
                    "*หลีกเลี่ยง: น้ำอัดลม น้ำหวาน\n"
                    "ขนมหวาน อาหารทอด\n"
                    "*ส่งพบแพทย์เพื่อตรวจ\n"
                    "ระดับน้ำตาล/ไขมัน"
                ),
                "ตัวอย่างเมนูรายวัน": (
                    "ข้าวกล้อง+ผักต้ม+ปลานึ่ง /\n"
                    "ซุปผักใส+ไก่ /\n"
                    "แอปเปิ้ล/ฝรั่ง /\n"
                    "นมจืดพร่องมันเนย"
                ),
                "การติดตาม": (
                    "ชั่งน้ำหนักทุก 2 สัปดาห์\n"
                    "ส่งพบแพทย์/นักโภชนาการ\n"
                    "ติดตามสุขภาพเมตาบอลิก"
                ),
            },
        ]

        def get_nutrition_row_style(row_key: str, current_category: str) -> str:
            if row_key != current_category:
                return "background:#FFFFFF;"

            if current_category == "normal":
                return (
                    "background:#D9F7D9;"
                    "border-left:6px solid #00C851;"
                    "font-weight:600;"
                )

            if current_category in ["overweight", "very_overweight"]:
                return (
                    "background:#FF8A8A;"
                    "border-left:6px solid #FF4B4B;"
                    "font-weight:600;"
                )

            if current_category == "underweight":
                return (
                    "background:#FFF7C2;"
                    "border-left:6px solid #FDD835;"
                    "font-weight:600;"
                )

            if current_category == "very_underweight":
                return (
                    "background:#FFE0B2;"
                    "border-left:6px solid #FF9800;"
                    "font-weight:600;"
                )

            return "background:#FFFFFF;"

        header_style = (
            "background:#1f4e79;"
            "color:white;"
            "font-weight:bold;"
            "padding:8px 10px;"
            "border:1px solid #ccc;"
            "text-align:center;"
            "font-size:0.85em;"
        )

        cell_style = (
            "padding:8px 10px;"
            "border:1px solid #ddd;"
            "vertical-align:top;"
            "font-size:0.82em;"
            "white-space:pre-wrap;"
        )

        cols_th = [
            "กลุ่ม",
            "เป้าหมาย",
            "คำแนะนำ",
            "หลักเลี่ยง / เสริม",
            "ตัวอย่างเมนูรายวัน",
            "การติดตาม",
        ]

        th_html = "".join(
            f'<th style="{header_style}">{col}</th>'
            for col in cols_th
        )

        rows_html = ""

        for row in NUTRITION_TABLE:
            row_key = row.get("key", "")
            row_style = get_nutrition_row_style(row_key, category)

            rows_html += f'<tr style="{row_style}">'

            for col in cols_th:
                rows_html += f'<td style="{cell_style}">{row.get(col, "")}</td>'

            rows_html += "</tr>"

        table_html = f"""
        <div style="overflow-x:auto;margin-top:16px;">
            <table style="
                width:100%;
                border-collapse:collapse;
                border:1px solid #ccc;
            ">
                <thead>
                    <tr>{th_html}</tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """

        st.markdown(table_html, unsafe_allow_html=True)

        st.caption(
            f"บันทึกโดย อสม.{vhv_name or '-'} | "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')} | "
            f"โรงพยาบาลพรหมคีรี"
        )


# ─── Sidebar: Records viewer ──────────────────────────────────────────────────
with st.sidebar:
    st.header("📁 ข้อมูลที่บันทึกแล้ว")

    records = load_records()

    if records:
        st.caption(f"ทั้งหมด {len(records)} รายการ")

        for i, rec in enumerate(records):
            child_name_display = str(rec.get("child_name", "-"))
            timestamp_display = str(rec.get("timestamp", ""))[:10]

            label = f"{child_name_display} | {timestamp_display}"

            with st.expander(label):
                st.write(f"**เพศ:** {rec.get('sex', '-')}")
                st.write(f"**อายุ:** {rec.get('age_total_months', '-')} เดือน")
                st.write(f"**น้ำหนัก:** {rec.get('weight_kg', '-')} กก.")
                st.write(f"**ผล:** {rec.get('result', '-')}")

                if st.button(f"🗑️ ลบรายการนี้", key=f"del_{i}"):
                    try:
                        delete_record(i)
                        st.success("ลบรายการเรียบร้อยแล้ว")
                        st.rerun()
                    except Exception as e:
                        st.error(f"ลบรายการไม่สำเร็จ: {e}")

        df = pd.DataFrame(records)
        csv = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "⬇️ ดาวน์โหลด CSV",
            csv,
            file_name="wcc_records.csv",
            mime="text/csv",
        )

    else:
        st.info("ยังไม่มีข้อมูล")


# ─── Footer ───────────────────────────────────────────────────────────────────
st.divider()

st.markdown(
    """
    <div style="text-align:center;line-height:2.2;color:#aaa;font-size:0.9em;">
        <strong>ด้วยความปรารถนาดี<br>
        <strong>คลินิกสุขภาพเด็กดี(WBC) โรงพยาบาลพรหมคีรี</strong><br>
        <strong>เปิดบริการ วันอังคาร เวลา 08.30-12.00น.<br>
        <strong>กลุ่มงานบริการด้านปฐมภูมิและองค์รวม<br>
        <strong>โทรศัพท์ 075-396023 &nbsp;|&nbsp; Fax 075-396463
    </div>
    """,
    unsafe_allow_html=True,
)