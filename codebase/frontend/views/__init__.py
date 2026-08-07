"""Các trang của ứng dụng.

⚠️ Cố ý KHÔNG đặt tên thư mục là `pages/`: Streamlit tự quét thư mục `pages/` cạnh entrypoint
để sinh multipage navigation riêng, sẽ đè lên sidebar tùy biến của app này.

Mỗi module ở đây export một hàm `render()` không tham số, đọc/ghi state qua st.session_state.
"""
