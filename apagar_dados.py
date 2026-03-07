import sqlite3


def apagar_dados():
    conn = sqlite3.connect("database/bd_bora_contratar.db")
    cursor = conn.cursor()
    
    cursor.execute("delete FROM candidaturas where id > 0")
    
    conn.commit()
    conn.close()

    return "Dados apagados com sucesso!"


if __name__ == "__main__":
    print(apagar_dados())