from typing import Optional

from sqlmodel import SQLModel

class BoletoModel(SQLModel):

    schema_db: str
    id_fatura: str
    status_fatura: Optional[str]
    url_boleto: Optional[str]