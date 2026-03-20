from database import Database
from datetime import datetime

class User:

  def __init__(self, email:str):
    self.__email = email
    self.__db = Database()
    __user = self.__db.get_user_by_email(email)
    self.__id = __user['id']
    self.__first_name = __user['first_name']
    self.__last_name = __user['last_name']
    self.__is_email_verified = __user['is_email_verified']
    self.__created_at = __user['created_at']

  def get_name(self):
    """ Returns: first_name, last_name """
    return self.__first_name, self.__last_name
  
  def get_email(self) -> str:
    return self.__email
  
  def get_is_email_verified(self)-> bool:
    return self.__is_email_verified

  def get_created_at(self) -> datetime:
    return datetime.fromtimestamp(self.__created_at)
  
  def get_all_info(self) -> dict:
    content = {
      'first_name': self.__first_name,
      'last_name': self.__last_name,
      'email': self.__email,
      'is_email_verified': self.__is_email_verified,
      'created_at': datetime.fromtimestamp(self.__created_at)
    }
    return content

  def set_name(self, first_name:str, last_name:str):
    # нужна валидация на спец символы и прочее для предотвращения траблов с бд
    self.__first_name = first_name
    self.__last_name = last_name
    self.__db.change_userName_by_id(self.__id,self.__first_name, self.__last_name)
    