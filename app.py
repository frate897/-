import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# ================= 1. 连接云数据库 =================
# 线上部署时，我们会把这两个敏感信息安全地存放在平台的 Secrets 中
# 如果你在本地测试，可以直接把第一步获取的 URL 和 KEY 粘贴到引号里
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "你的_SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "你的_SUPABASE_KEY")

# 初始化 Supabase 客户端
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("数据库连接配置错误，请检查 URL 和 KEY 填写的对不对。")

# ================= 2. 页面配置 =================
st.set_page_config(page_title="餐馆财务云共享系统", layout="wide", page_icon="🍽️")
st.title("🍽️ 餐馆收支线上云共享系统")
st.caption("数据云端加密存储 · 支持异地多人同时记账")

# ================= 3. 侧边栏：添加账目 =================
st.sidebar.header("➕ 记一笔新账")

with st.sidebar.form("ledger_form", clear_on_submit=True):
    input_date = st.date_input("选择日期", datetime.now())
    input_type = st.selectbox("账目类型", ["收入", "支出"])
    input_amount = st.number_input("金额 (元)", min_value=0.01, step=0.01, format="%.2f")
    input_reason = st.text_input("原因 / 备注", placeholder="如：采购牛肉、美团外卖结算等")
    
    submit_btn = st.form_submit_button("发送到云端保存")

if submit_btn:
    if input_reason.strip() == "":
        st.sidebar.error("❌ 请填写账目原因！")
    elif input_amount <= 0:
        st.sidebar.error("❌ 金额必须大于 0！")
    else:
        # 将数据写入 Supabase 云数据库里的 ledger 表
        data_to_insert = {
            "date": input_date.strftime('%Y-%m-%d'),
            "type": input_type,
            "amount": input_amount,
            "reason": input_reason
        }
        try:
            supabase.table("ledger").insert(data_to_insert).execute()
            st.sidebar.success(f"✅ 已成功同步到云端！")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"保存失败，请检查数据库。错误信息: {e}")

# ================= 4. 主面板：从云端读取数据 =================
try:
    # 从云端读取所有账目，按日期和 ID 降序排列
    response = supabase.table("ledger").select("*").order("date", descending=True).order("id", descending=True).execute()
    records = response.data
    df_raw = pd.DataFrame(records)
    
    if not df_raw.empty:
        # 重命名列名让前端显示更好看
        df = df_raw.rename(columns={
            "date": "日期",
            "type": "类型",
            "amount": "金额",
            "reason": "原因_备注"
        })
        
        # --- 财务数据统计 ---
        total_income = df[df["类型"] == "收入"]["金额"].sum()
        total_expense = df[df["类型"] == "支出"]["金额"].sum()
        net_profit = total_income - total_expense

        # --- 顶部财务看板 ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div style='padding:15px; border-radius:10px; background-color:#e8f5e9; border-left:5px solid #2e7d32;'><p style='margin:0; color:#2e7d32; font-size:14px;'>💰 累计总收入</p><h2 style='margin:0; color:#1b5e20;'>￥{total_income:,.2f}</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='padding:15px; border-radius:10px; background-color:#ffebee; border-left:5px solid #c62828;'><p style='margin:0; color:#c62828; font-size:14px;'>💸 累计总支出</p><h2 style='margin:0; color:#b71c1c;'>￥{total_expense:,.2f}</h2></div>", unsafe_allow_html=True)
        with col3:
            profit_color = "#1b5e20" if net_profit >= 0 else "#b71c1c"
            profit_bg = "#e8f5e9" if net_profit >= 0 else "#ffebee"
            st.markdown(f"<div style='padding:15px; border-radius:10px; background-color:{profit_bg}; border-left:5px solid {profit_color};'><p style='margin:0; color:{profit_color}; font-size:14px;'>📈 净结余 (利润)</p><h2 style='margin:0; color:{profit_color};'>￥{net_profit:,.2f}</h2></div>", unsafe_allow_html=True)

        st.markdown("---")

        # --- 历史账目明细表格 ---
        st.subheader("📋 历史实时账目明细")
        
        # 导出 Excel/CSV 备份
        csv_data = df[["日期", "类型", "金额", "原因_备注"]].to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 下载数据备份 (CSV)", data=csv_data, file_name=f"餐馆财务明细_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')
        
        # 显示表格
        st.dataframe(
            df[["日期", "类型", "金额", "原因_备注"]],
            use_container_width=True,
            column_config={
                "金额": st.column_config.NumberColumn("金额 (元)", format="￥%.2f"),
                "日期": st.column_config.DateColumn("日期")
            }
        )
    else:
        st.info("💡 目前云端数据库为空。请在左侧边栏输入数据，开启你们的第一笔记账吧！")

except Exception as e:
    st.info("💡 首次使用提示：请先前往 Supabase 数据库创建一个名为 `ledger` 的表，或者检查网络连接。")