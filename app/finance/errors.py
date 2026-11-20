"""Hesaplama modülüne ait doğrulama hataları."""


class ValidationError(ValueError):
    """Kullanıcı girdisi geçersiz olduğunda fırlatılır.

    ``field`` hatanın hangi alandan kaynaklandığını, mesaj ise kullanıcıya
    gösterilecek Türkçe açıklamayı içerir.
    """

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message
