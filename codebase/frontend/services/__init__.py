"""Tầng service của frontend.

Quy ước quan trọng: module trong đây KHÔNG được import `ui` hay `views` — chiều phụ thuộc
luôn là `config <- api_client <- services <- ui <- views <- app`. Giữ đúng chiều này thì
service unit-test được mà không cần dựng Streamlit.
"""
