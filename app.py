import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

# ==================== 把你的钥匙贴在下面 ====================
# 把引文里的内容，换成你刚刚在微信里备用的那两串长字符！
SUPABASE_URL = "https://ubmaolxyxrdcpxlbqhje.supabase.co"
SUPABASE_KEY = "ubmaolxyxrdcpxlbqhje"
# ==========================================================

# 1. 自动连接网上的账本
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("连接失败，请检查上面的两条钥匙是否复制完整！")
    st.stop()

# 2. 网页的标题和样式
st.set_page_config(page_title="餐馆财务云共享", layout="wide")
st.title("🍽️ 餐馆收支线上云共享系统")

# 3. 左侧填写记账的地方
st.sidebar.header("➕ 记一笔新账")
with st.sidebar.form("ledger_form", clear_on_submit=True):
    input_date = st.date_input("选择日期", datetime.now())
    input_type = st.selectbox("账目类型", ["收入", "支出"])
    input_amount = st.number_input("金额 (元)", min_value=0.01, step=0.01)
    input_reason = st.text_input("原因 / 备注", placeholder="如：买菜、房租、外卖结算")
    submit_btn = st.form_submit_button("发送到云端账本")

# 当点击“发送”按钮时，程序把数据打包送到网上的 Supabase 账本里
if submit_btn:
    if not input_reason.strip():
        st.sidebar.error("请填写原因")
    else:
        data = {
            "date": input_date.strftime('%Y-%m-%d'),
            "type": input_type,
            "amount": input_amount,
            "reason": input_reason
        }
        supabase.table("ledger").insert(data).execute()
        st.sidebar.success("✅ 成功传送到云端账本！")
        st.rerun()

# 4. 右侧从网上账本读取数据显示出来
try:
    res = supabase.table("ledger").select("*").order("date", descending=True).execute()
    if res.data:
        df = pd.DataFrame(res.data).rename(columns={"date":"日期","type":"类型","amount":"金额","reason":"原因"})
        
        # 计算总数
        in_sum = df[df["类型"] == "收入"]["金额"].sum()
        ex_sum = df[df["类型"] == "支出"]["金额"].sum()
        
        # 显示三个大方块看板
        c1, c2, c3 = st.columns(3)
        c1.metric("💰 总收入", f"￥{in_sum:,.2f}")
        c2.metric("💸 总支出", f"￥{ex_sum:,.2f}")
        c3.metric("📈 净利润", f"￥{in_sum - ex_sum:,.2f}")
        
        # 显示明细表格
        st.write("---")
        st.dataframe(df[["日期", "类型", "金额", "原因"]], use_container_width=True)
    else:
        st.info("💡 账本目前是空的，在左边记一笔试试吧！")
except Exception as e:
  except Exception as e:
    st.error(f"❌ 报错啦！具体失败原因如下，请看这里：")
    st.code(str(e)) # 这行代码会把真正的错误原因用黑框打印在网页上
    st.info("💡 提示：如果上面显示 'invalid_api_key'，说明是 SUPABASE_KEY 贴错了；如果显示 'endpoint not found'，说明是 SUPABASE_URL 贴错了。")
