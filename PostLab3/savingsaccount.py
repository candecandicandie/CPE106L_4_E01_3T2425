"""
Combined bank and savings account module.
"""

import pickle
import random

class SavingsAccount(object):
    """Represents a savings account with owner's name, PIN, and balance."""

    RATE = 0.02  # Interest rate for all accounts

    def __init__(self, name, pin, balance=0.0):
        self.name = name
        self.pin = pin
        self.balance = balance

    def __str__(self):
        """String representation of the account."""
        result = 'Name:    ' + self.name + '\n'
        result += 'PIN:     ' + self.pin + '\n'
        result += 'Balance: ' + str(self.balance)
        return result

    def getBalance(self):
        return self.balance

    def getName(self):
        return self.name

    def getPin(self):
        return self.pin

    def deposit(self, amount):
        if amount < 0:
            return "Amount must be >= 0"
        self.balance += amount
        return None

    def withdraw(self, amount):
        if amount < 0:
            return "Amount must be >= 0"
        elif self.balance < amount:
            return "Insufficient funds"
        else:
            self.balance -= amount
            return None

    def computeInterest(self):
        interest = self.balance * SavingsAccount.RATE
        self.deposit(interest)
        return interest

    def __lt__(self, other):
        """Enable sorting by name."""
        return self.name < other.name


class Bank:
    """Represents a bank with a collection of savings accounts."""

    def __init__(self, fileName=None):
        self.accounts = {}
        self.fileName = fileName
        if fileName is not None:
            with open(fileName, "rb") as fileObj:
                while True:
                    try:
                        account = pickle.load(fileObj)
                        self.add(account)
                    except EOFError:
                        break

    def __str__(self):
        """Return string of all accounts sorted by name."""
        sorted_accounts = sorted(self.accounts.values())
        return "\n\n".join(str(account) for account in sorted_accounts)

    def makeKey(self, name, pin):
        return name + "/" + pin

    def add(self, account):
        key = self.makeKey(account.getName(), account.getPin())
        self.accounts[key] = account

    def remove(self, name, pin):
        key = self.makeKey(name, pin)
        return self.accounts.pop(key, None)

    def get(self, name, pin):
        key = self.makeKey(name, pin)
        return self.accounts.get(key, None)

    def computeInterest(self):
        total = 0
        for account in self.accounts.values():
            total += account.computeInterest()
        return total

    def save(self, fileName=None):
        if fileName is not None:
            self.fileName = fileName
        if self.fileName is None:
            return
        with open(self.fileName, "wb") as fileObj:
            for account in self.accounts.values():
                pickle.dump(account, fileObj)


def createBank(numAccounts=1):
    names = ("Brandon", "Molly", "Elena", "Mark", "Tricia",
             "Ken", "Jill", "Jack")
    bank = Bank()
    upperPin = numAccounts + 1000
    for pinNumber in range(1000, upperPin):
        name = random.choice(names)
        balance = float(random.randint(100, 1000))
        bank.add(SavingsAccount(name, str(pinNumber), balance))
    return bank


def testAccount():
    account = SavingsAccount("Ken", "1000", 500.00)
    print(account)
    print(account.deposit(100))
    print("Expect 600:", account.getBalance())
    print(account.deposit(-50))  # Should return error message
    print("Expect 600:", account.getBalance())
    print(account.withdraw(100))
    print("Expect 500:", account.getBalance())
    print(account.withdraw(-50))  # Should return error message
    print("Expect 500:", account.getBalance())
    print(account.withdraw(100000))  # Should return error message
    print("Expect 500:", account.getBalance())


def main(number=10, fileName=None):
    testAccount()
    if fileName:
        bank = Bank(fileName)
    else:
        bank = createBank(number)
    print("\nAccounts in sorted order:\n")
    print(bank)


if __name__ == "__main__":
    main()
