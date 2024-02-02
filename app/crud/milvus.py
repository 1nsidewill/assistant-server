#config import
from config import Settings

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



conf = Settings()

#Milvus connect info
HOST = conf.milvus_HOST
PORT = conf.milvus_PORT
USER = conf.milvus_USER
PW = conf.milvus_PW
database = conf.milvus_Database

#postgresql connect info
postgre_HOST = conf.postgre_HOST
postgre_PORT = conf.postgre_PORT
postgre_DB = conf.postgre_DB
postgre_USER = conf.postgre_USER
postgre_PW = conf.postgre_PW

#Hyper Clover X connect info
hcx_mode = conf.hcx_mode
hcx_app_id = conf.hcx_app_id
hcx_model_name = conf.hcx_model_name
hcx_api_base = conf.hcx_api_base
hcx_clovastudio_api_key = conf.hcx_clovastudio_api_key
hcx_apigw_api_key = conf.hcx_apigw_api_key

#Milvus connect info
milvus_HOST = conf.milvus_HOST
milvus_PORT = conf.milvus_PORT
milvus_Database = conf.milvus_Database
milvus_USER = conf.milvus_USER
milvus_PW = conf.milvus_PW


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
# Connect Milvus
# ==================================================================
def connect_milvus():    
    #get hcx embedding
    embeddings = HCXEmbeddings(
        app_id=hcx_app_id,
        model_name=hcx_model_name,
        api_base=hcx_api_base,
        clovastudio_api_key=hcx_clovastudio_api_key,
        apigw_api_key=hcx_apigw_api_key,
    )
    
    #connect milvus
    vector_db = Milvus(
        embeddings,
        connection_args={"host":milvus_HOST, "port":milvus_PORT, "user":milvus_USER, "password":milvus_PW, "db_name":milvus_Database},
        collection_name = milvus_collection_name,
        #collection_name = "langtest",
    )
    print("Milvus Connect !!")
    return vector_db


# ==================================================================
# insert data into Milvus
# ==================================================================
def insert_milvus(gvector_db, ginsert_docs):
    print("Insert Data into Milvus Start!!")    
    gvector_db.add_documents(ginsert_docs)
    print("Insert Data into Milvus Finish!!")


# ==================================================================
# recreate Milvus collection
# ==================================================================
def recreate_milvus_collection():
    print("Milvus Connect Start!!")
    connections.connect(    
        user=USER,
        password=PW,
        host=HOST,
        port=PORT,
        db_name=database,
    )

    utility.drop_collection(milvus_collection_name)

    #collection schema   
    pk = FieldSchema(
    name="pk",
    dtype=DataType.INT64,
    is_primary=True,    
    auto_id=True,
    ) 
    vector = FieldSchema(
    name="vector",
    dtype=DataType.FLOAT_VECTOR,
    dim=1024,
    )
    domain_id = FieldSchema(
    name="domain_id",
    dtype=DataType.INT64,
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
        name = milvus_collection_name,
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




#connect milvus
vector_db = connect_milvus()

#recreate milvus collection(domain_desc)
#recreate_milvus_collection()

#get domain list in postgresql
domain_list = check_domain_in_pg()

#create domain document list
documents = create_domain_document(domain_list)
split_documents = split_documents(documents)

print(split_documents)

#insert_milvus(vector_db, documents)
insert_milvus(vector_db, split_documents)



