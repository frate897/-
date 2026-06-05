import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# ==================== 1. 填写你的云账本钥匙 ====================
SUPABASE_URL = "https://ubmaolxyxrdcpxlbqhje.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVibWFvbHh5eHJkY3B4bGJxaGplIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2ODY0MDIsImV4cCI6MjA5NjI2MjQwMn0.5I0hYyf3LU5-uf2YHqJr9Ak67gj_TFQxauFT4efylFE"
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
    # 读取所有数据（包含数据库里每条账目独有的 id，用来精准删除）
    res = supabase.table("ledger").select("*").order("date", desc=True).execute()
    
    if res.data:
        df_raw = pd.DataFrame(res.data)
        
        # 计算总收入与总支出
        in_sum = df_raw[df_raw["type"] == "收入"]["amount"].sum()
        ex_sum = df_raw[df_raw["type"] == "支出"]["amount"].sum()
        
        # 顶部三个大方块看板
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 总收入", f"￥{in_sum:,.2f}")
        c2.metric("💸 总支出", f"￥{ex_sum:,.2f}")
        c3.metric("📈 净利润", f"￥{in_sum - ex_sum:,.2f}")
        
        st.write("---")
        st.subheader("📋 历史明细与操作")
        
        # 💡 核心新增：用循环的方式把账目一条条显示出来，并在每条账目后面配一个删除按钮
        for index, row in df_raw.iterrows():
            # 创建4个并排的列，前3列显示账目内容，第4列放删除按钮
            col_info, col_amt, col_reason, col_btn = st.columns([2, 2, 4, 1])
            
            with col_info:
                # 区分收入和支出的显示颜色
                emoji = "🟢 收入" if row['type'] == "收入" else "🔴 支出"
                st.write(f"**{row['date']}** {emoji}")
            with col_amt:
                st.write(f"**￥{row['amount']:.2f}**")
            with col_reason:
                st.write(f"{row['reason']}")
            with col_btn:
                # 每条账目自带一个专属的删除按钮，绑定它在数据库里的 id
                if st.button("🗑️ 删除", key=f"del_{row['id']}"):
                    try:
                        # 去云端数据库里，把这个 id 的那一行删掉
                        supabase.table("ledger").delete().eq("id", row['id']).execute()
                        st.toast("👋 账目已成功删除！")
                        st.rerun() # 刷新网页
                    except Exception as del_err:
                        st.error(f"删除失败: {del_err}")
                        
    else:
        st.info("💡 账本目前是空的，在左边记一笔试试吧！")
except Exception as read_error:
    st.error("❌ 读取数据失败！")
    st.code(str(read_error))
