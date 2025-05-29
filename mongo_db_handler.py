from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi


class MongoDBHandler:
    def __init__(self, uri, db_name):
        self.__client = MongoClient(uri)
        # Send a ping to confirm a successful connection
        try:
            self.__client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

        self.__db = self.__client[db_name]
        self.__pi_data_map = {} # maps keys to their respective collection

    def sensor_field_doc_temp(self, sensor_id, sensor_type, sensor_value, sensor_unit):
        return {
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'sensor_value': sensor_value,
            'sensor_unit': sensor_unit
        }
    
    def actuator_field_doc_temp(self, actuator_id, actuator_type, actuator_value):
        return {
            'actuator_id': actuator_id,
            'actuator_type': actuator_type,
            'actuator_value': actuator_value
        }

    def create_collection(self, collection_name, key, fields):
        self.__pi_data_map[key] = {
            'collection': self.__db[collection_name],
            'fields': fields           
        }

    def insert_sensor_data(self, key, sensor_value):
        self.__pi_data_map[key]['fields']['sensor_value'] = sensor_value
        self.__pi_data_map[key]['collection'].insert_one(self.__pi_data_map[key]['fields'])

    def insert_actuator_data(self, key, actuator_value):
        self.__pi_data_map[key]['fields']['actuator_value'] = actuator_value
        self.__pi_data_map[key]['collection'].insert_one(self.__pi_data_map[key]['fields'])

    def insert_image_data(self, key, image_path, timestamp):
        self.__pi_data_map[key]['fields']['image'] = image_path
        self.__pi_data_map[key]['fields']['timestamp'] = timestamp
        self.__pi_data_map[key]['collection'].insert_one(self.__pi_data_map[key]['fields'])

    def get_data(self, key):
        return self.__pi_data_map[key]['collection'].find_one()
    
    def get_all_data(self, key):
        return self.__pi_data_map[key]['collection'].find()
    
    def delete_data(self, key):
        self.__pi_data_map[key]['collection'].delete_many({})

    def delete_all_data(self):
        self.__db.drop()

    def close_connection(self):
        self.__client.close()

    