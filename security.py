import jwt
from datetime import datetime,timedelta

SECRET_KEY = 'my-super-secret-key-for-AlkozaySchool-app-2026'
ALGORITHM = 'HS256'

def create_access_token(data:dict):
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({'exp': expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)
    
    return encoded_jwt
    
def decode_access_token(token:str):
    try:
        decode_jwt = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        return decode_jwt
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None