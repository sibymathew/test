from mongoengine import *
import json

class Account(DynamicDocument):
    username = StringField(required=True,unique=True)
    email = EmailField(required=True,unique=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    password = StringField(required=True)
    company = StringField()
    phone = StringField()
    send_notification = BooleanField()
    is_enabled = BooleanField(default=True)

    @classmethod
    def parseForCreate(cls,req):
        """
            Parsing of a json request and will create a 
            Account object.

            Validation will happen when save is called.

            This is basically parsing part of serializer.

            This should raise errors when the required fields
            are not present.

        """

        presenceList = ['username','first_name','last_name',
            'password','email']
        for key in presenceList:
            if not req.get(key): raise Exception('Required param missing')

        newAccount = cls()
        newAccount.username = req.get('username')
        newAccount.first_name = req.get('first_name')
        newAccount.last_name = req.get('last_name')
        newAccount.company = req.get('company')
        newAccount.email = req.get('email')
        newAccount.password = req.get('password')
        newAccount.send_notification = req.get('send_notification',True)

        # is_active should start with false. Confirmation email will set it True.
        # deactivation/reactivation will set it false/true later.
        # and, this workflow needs to be coded up.
        newAccount.is_enabled = True
        # phone is optional.
        if req.get('phone'):
            newAccount.phone = req.get('phone')

        # print (newAccount.to_json())
        return newAccount

    def updateAccount(self,req):
        """
            Validate the json String
            extract parameters
            fetch and instantiate the object
            return the object.
        """
        allParams= ['username','first_name','last_name',
            'password','email','company']
        req
        for param in allParams:
            if req.get(param):
                setattr(self,param,req.get(param))
        return self

    def clean(self,**kwargs):
        super(Account,self).clean(**kwargs)


class AccountList():
    """
        Created a new type to make a list of accounts serializable.
    """
    def __init__(self):
        self.accountList = []

    def append(self,ele):
        """
            Appends an element to list.
        """
        self.accountList.append(ele)
    def to_json(self):
        """
            returns a json string for account list.
        """
        print (self.accountList[0].to_json())
        return '['+''.join(
            [account.to_json() for account in self.accountList])+']'

    def __str__(self):
        return __name__

#we need an anonymous account. So, set to this username.
anonymousAccount = lambda : Account(username='user121')