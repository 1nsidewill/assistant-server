#config import
from app.config import get_settings
#text loader
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
#embedding(HCX) import
from langchain_community.embeddings import HCXEmbeddings
#Milvus import 
from langchain_community.vectorstores import Milvus
from pymilvus import connections, CollectionSchema, FieldSchema, DataType, Collection, utility, db
#postgresql connect import
import psycopg2

from app.crud import schema



conf = get_settings()

#Milvus connect info
HOST = conf.milvus_host
PORT = conf.milvus_port
USER = conf.milvus_user
PW = conf.milvus_password
database = conf.milvus_db_name

#postgresql connect info
postgre_HOST = conf.postgre_HOST
postgre_PORT = conf.postgre_PORT
postgre_DB = conf.postgre_DB
postgre_USER = conf.postgre_USER
postgre_PW = conf.postgre_PW

#Hyper Clover X connect info
hcx_mode = conf.hcx_mode
hcx_app_id = conf.emb_app_id
hcx_model_name = conf.hcx_model_name
hcx_api_base = conf.emb_api_base
hcx_clovastudio_api_key = conf.emb_clovastudio_api_key
hcx_apigw_api_key = conf.emb_apigw_api_key

#Milvus connect info
milvus_HOST = conf.milvus_host
milvus_PORT = conf.milvus_port
milvus_Database = conf.milvus_db_name
milvus_USER = conf.milvus_user
milvus_PW = conf.milvus_password

#Milvus collection info
milvus_collection_name = "domain_desc"

# ==================================================================
# search uploading file data into postgresql 
# ==================================================================
def check_domain_in_pg():
    print("Check Domain in PG Start!!")
    #db connect
    pg_connection = psycopg2.connect(
        host = postgre_HOST,
        port = postgre_PORT,
        database = postgre_DB,
        user = postgre_USER,
        password = postgre_PW
    )

    cursor = pg_connection.cursor()
    try:
        #PGData Select
        select_sql =  " SELECT DOMAIN_ID, DOMAIN_NAME, DOMAIN_DESC "        
        select_sql += "   FROM DOMAIN "        
        cursor.execute(select_sql)        
        rows = cursor.fetchall()
        #print(rows)

        #get file info list
        insert_domain_list = [] 
        #print(rows)       
        for row in rows:
            domain_list = {}
            domain_list['domain_id'] = row[0]
            domain_list['domain_name'] = row[1]
            domain_list['domain_desc'] = row[2]
            insert_domain_list.append(domain_list)            
        
        #print(insert_file_list)
    except Exception as e:
        print("Error : " + str(e))

    cursor.close()
    pg_connection.close()
    print("Check Domain in PG Finish!!")
    return insert_domain_list


# ==================================================================
# Create Domain Document
# ==================================================================
def create_domain_document(domain_list):
    documents = []
    for domain in domain_list:
        #print(domain)
        document = Document(page_content=domain['domain_desc'], metadata={"source":"database", "domain_id":domain['domain_id'], "name":domain['domain_name'], "text":domain['domain_desc']})
        #print(document)
        documents.append(document)
    return documents


# ==================================================================
# re_split documents => set chunk size => split documents text
# ==================================================================
def split_documents(gdocuments):
    print("Result Split Start!!")
    #langchain split(RecursiveCharacterTextSplitter)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 400, chunk_overlap = 10)
    split_doc = text_splitter.split_documents(gdocuments)
    #print(split_doc)

    '''
    #use llama_index split(SentenceSplitter)
    text_splitter = SentenceSplitter(chunk_size=400, chunk_overlap=1)
    split_nodes: List[TextNode] = text_splitter.get_nodes_from_documents(gdocuments)
    '''
    print("Result Split Finish!!")
    return split_doc

# ==================================================================
# create id data for Milvus
# ==================================================================
def create_ids(insert_docs, field_name):
    print("Create ID Start!!")    
    ids = []
    for doc in insert_docs:                
        ids.append(str(doc.metadata[field_name]))
    print("Create ID Finish!!")
    return ids

# ==================================================================
# Connect Milvus
# ==================================================================
def connect_milvus(collection_name, partition_names=None):    
    #get hcx embedding
    embeddings = HCXEmbeddings(
        app_id=hcx_app_id,
        model_name=hcx_model_name,
        api_base=hcx_api_base,
        clovastudio_api_key=hcx_clovastudio_api_key,
        apigw_api_key=hcx_apigw_api_key,
    )
    
    #connect milvus
    if partition_names is not None:
        vector_db = Milvus(
            embeddings,
            connection_args={"host":milvus_HOST, "port":milvus_PORT, "user":milvus_USER, "password":milvus_PW, "db_name":milvus_Database},
            collection_name = collection_name,
            partition_names=partition_names
        )
    else:
        vector_db = Milvus(
            embeddings,
            connection_args={"host":milvus_HOST, "port":milvus_PORT, "user":milvus_USER, "password":milvus_PW, "db_name":milvus_Database},
            collection_name = collection_name,
        )
        
    print("Milvus Connect !!")
    return vector_db


# ==================================================================
# insert data into Milvus
# ==================================================================
def insert_milvus(gvector_db, ginsert_docs, gids):
    print("Insert Data into Milvus Start!!")    
    gvector_db.add_documents(ginsert_docs, ids=gids)
    print("Insert Data into Milvus Finish!!")


# ==================================================================
# recreate Milvus collection
# ==================================================================
def recreate_milvus_collection(collection_name):
    print("Milvus Connect Start!!")
    connections.connect(    
        user=USER,
        password=PW,
        host=HOST,
        port=PORT,
        db_name=database,
    )

    utility.drop_collection(collection_name)

    if collection_name == "domain_desc":
        #collection schema   
        pk = FieldSchema(
        name="pk",
        #dtype=DataType.INT64,
        dtype=DataType.VARCHAR,
        max_length=512,
        is_primary=True,    
        #auto_id=True,
        ) 
        vector = FieldSchema(
        name="vector",
        dtype=DataType.FLOAT_VECTOR,
        dim=1024,
        )
        domain_id = FieldSchema(
        name="domain_id",
        dtype=DataType.INT64
        )
        text = FieldSchema(
        name="text",
        dtype=DataType.VARCHAR,
        max_length=1024,
        )
        name = FieldSchema(
        name="name",
        dtype=DataType.VARCHAR,
        max_length=256,
        )
        schema = CollectionSchema(
            fields=[pk, vector, domain_id, text, name],
            description="domain milvus collection",
            enable_dynamic_field=True,
        )

        collection = Collection(    
            name = collection_name,
            schema=schema,
            using='default',
            shards_num=2,    
        )

        # index create
        index = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 1024},
        }
        collection.create_index("vector", index)
        print("File Input Collection Create Finish!!")
    elif collection_name == "api_desc":
        #collection schema   
        pk = FieldSchema(
        name="pk",
        #dtype=DataType.INT64,
        dtype=DataType.VARCHAR,
        max_length=512,
        is_primary=True,    
        #auto_id=True,
        ) 
        vector = FieldSchema(
        name="vector",
        dtype=DataType.FLOAT_VECTOR,
        dim=1024,
        )
        api_id = FieldSchema(
        name="api_id",
        dtype=DataType.INT64,
        )
        text = FieldSchema(
        name="text",
        dtype=DataType.VARCHAR,
        max_length=2048,
        )
        domain_id = FieldSchema(
        name="domain_id",
        dtype=DataType.INT64
        )
        # spec = FieldSchema(
        # name="spec",
        # dtype=DataType.VARCHAR,
        # max_length=4096,
        # )
        # system_id = FieldSchema(
        # name="system_id",
        # dtype=DataType.INT64,
        # )
        
        schema = CollectionSchema(
            fields=[pk, vector, api_id, text, domain_id],
            description="api_spec milvus collection",
            enable_dynamic_field=True,
            partition_key_field="domain_id"
        )

        collection = Collection(    
            name = collection_name,
            schema=schema,
            using='default',
            shards_num=2,    
        )

        # index create
        index = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 1024},
        }
        
        collection.create_index("vector", index)
        collection.load()
        print("File Input Collection Create Finish!!")        


def insert_test_data(item:schema.ApiDescItem):
    documents = []
    document = Document(page_content=item.text, metadata={"source":"database", "domain_id":item.domain_id, "api_id":item.api_id, "text":item.text})
        #print(document)
    documents.append(document)
    
    return documents