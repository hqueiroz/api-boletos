import psycopg2
#import paramiko
#from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder
from core.secrets import JUMP_HOST, JUMP_KEY, JUMP_USER, RDS_DBNAME,RDS_HOST,RDS_PASSWORD,RDS_USER

# Função para criar a conexão com o banco de dados PostgreSQL

def create_ssh_tunnel():
    # Informações do servidor SSH (Instância EC2)
    ssh_host = JUMP_HOST  # IP público da instância EC2
    ssh_user = JUMP_USER  # Usuário SSH
    ssh_key = JUMP_KEY  # Caminho para a chave privada SSH

    # Informações do banco de dados PostgreSQL RDS
    rds_host = RDS_HOST  # Endpoint do RDS
    rds_port = 5432  # Porta do PostgreSQL no RDS
    local_port = 5433  # Porta local onde o túnel vai escutar

    # Criando o túnel SSH usando Paramiko e SSHTunnelForwarder
    tunnel = SSHTunnelForwarder(
        (ssh_host, 22),
        ssh_username=ssh_user,
        ssh_pkey=ssh_key,
        remote_bind_address=(rds_host, rds_port),
        local_bind_address=('127.0.0.1', local_port)
    )

    tunnel.start()
    return tunnel, local_port

def connect_to_postgresql(local_port):
    # Informações de conexão com o PostgreSQL
    db_user = RDS_USER
    db_password = RDS_PASSWORD
    db_name = RDS_DBNAME
    
    # Conectar ao banco de dados via túnel local
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host='127.0.0.1',  # Acesso via localhost (túnel SSH)
        port=local_port
    )
    return conn

def main():
    # Criar túnel SSH
    tunnel, local_port = create_ssh_tunnel()
    
    # Conectar ao banco de dados PostgreSQL
    conn = connect_to_postgresql(local_port)
    
    # Criar um cursor para realizar consultas
    cursor = conn.cursor()
    
    # Executar uma consulta SQL
    cursor.execute('SELECT ds_sigla FROM fenapro.tb_entidade LIMIT 10;')
    rows = cursor.fetchall()
    print(rows)
    
    # Fechar a conexão e o túnel
    cursor.close()
    conn.close()
    tunnel.stop()

if __name__ == "__main__":
    main()