import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# ==================== 1. 填写你的云账本钥匙 ====================
SUPABASE_URL = "https://ubmaolxyxrdcpxlbqhje.supabase.co"
SUPABASE_KEY = "ubmaolxyxrdcpxlbqhje"
# =============================================================

# 自动连接网上的账本
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("初始化连接失败，请检查钥匙是否完整。")
    st.stop()

# 页面配置
st.set_page_config(page_title="餐馆财务云共享", layout="wide")
st.title("🍽️ 餐馆收支线上云共享系统")

# 左侧侧边栏：填写记账
st.sidebar.header("➕ 记一笔新账")
with st.sidebar.form("ledger_form", clear_on_submit=True):
    input_date = st.date_input("选择日期", datetime.now())
    input_type = st.selectbox("账目类型", ["收入", "支出"])
    input_amount = st.number_input("金额 (元)", min_value=0.01, step=0.01)
    input_reason = st.text_input("原因 / 备注", placeholder="如：买菜、房租、外卖结算")
    submit_btn = st.form_submit_button("发送到云端账本")

if submit_btn:
    if not input_reason.strip():
        st.sidebar.error("请填写原因")
    else:
        try:
            data = {
                "date": input_date.strftime('%Y-%m-%d'),
                "type": input_type,
                "amount": input_amount,
                "reason": input_reason
            }
            supabase.table("ledger").insert(data).execute()
            st.sidebar.success("✅ 成功传送到云端！")
            st.rerun()
        except Exception as insert_error:
            st.sidebar.error(f"保存失败: {insert_error}")

# 右侧主面板：读取并显示数据
try:
    # 💡 修正的地方：把 descending=True 改成了 desc=True
    res = supabase.table("ledger").select("*").order("date", desc=True).execute()
    
    if res.data:
        df = pd.DataFrame(res.data).rename(columns={"date": "日期", "type": "类型", "amount": "金额", "reason": "原因"})
        
        # 计算总收入与总支出
        in_sum = df[df["类型"] == "收入"]["金额"].sum()
        ex_sum = df[df["类型"] == "支出"]["金额"].sum()
        
        # 顶部三个大方块看板
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 总收入", f"￥{in_sum:,.2f}")
        c2.metric("💸 总支出", f"￥{ex_sum:,.2f}")
        c3.metric("📈 净利润", f"￥{in_sum - ex_sum:,.2f}")
        
        # 显示历史明细表格
        st.write("---")
        st.dataframe(df[["日期", "类型", "金额", "原因"]], use_container_width=True)
    else:
        st.info("💡 账本目前是空的，在左边记一笔试试吧！")
except Exception as read_error:
    st.error("❌ 读取数据失败！具体错误原因如下：")
    st.code(str(read_error))
