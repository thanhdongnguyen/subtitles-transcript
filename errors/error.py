from flask import g

error_define = {
    403: {
        "en": "Forbidden",
        "vi": "Không được phép truy cập"
    },
    500: {
        "en": "Internal Server Error",
        "vi": "Lỗi máy chủ"
    },
    10: {
        "en": "Email is existed",
        "vi": "Email đã tồn tại"
    },
    11: {
        "en": "Account isn't existed",
        "vi": "Tài khoản không tồn tại"
    },
    12: {
        "en": "Account/Password is incorrect",
        "vi": "Tài khoản/Mật khẩu không chính xác"
    },
    13: {
        "en": "Register successfully",
        "vi": "Đăng ký thành công"
    },
    14: {
        "en": "Login successfully",
        "vi": "Đăng nhập thành công"
    },
    15: {
        "en": "Account isn't existed",
        "vi": "Tài khoản không tồn tại"
    },
    16: {
        "en": "Account is blocked",
        "vi": "Tài khoản bị khóa"
    },
    17: {
        "en": "Parameters Invalid",
        "vi": "Tham số không hợp lệ"
    },
    18: {
        "en": "Info Account Update Invalid",
        "vi": "Thông tin cập nhật tài khoản không hợp lệ"
    },
    19: {
        "en": "Video not found",
        "vi": "Video không tồn tại"
    },
    20: {
        "en": "File not valid",
        "vi": "File không hợp lệ"
    },
    21: {
        "en": "Project not found",
        "vi": "Dự án không tồn tại"
    },
    22: {
        "en": "Can't start process this project",
        "vi": "Không thể bắt đầu xử lý dự án này"
    },
    23: {
        "en": "Link youtube invalid",
        "vi": "Link youtube không hợp lệ"
    },
    24: {
        "en": "Can't get subtitles of info of link youtube",
        "vi": "Không thể lấy phụ đề của link youtube"
    },
    25: {
        "en": "Current, not support subtitle with this language",
        "vi": "Hiện tại, không hỗ trợ phụ đề với ngôn ngữ này"
    },
    26: {
        "en": "Can't not download video",
        "vi": "Không thể tải video"
    },


}


def get_error(code: int, lang: str = "vi") -> dict:
    if "lang" in g:
        lang = g.lang
    err = error_define[code][lang]

    return {
        "message": err,
        "code": code
    }