import json
from collections import UserDict, defaultdict
from datetime import datetime, timedelta

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not isinstance(value, str) or not value.isdigit() or len(value) != 10:
            raise ValueError("Invalid phone number format.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d-%m-%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD-MM-YYYY.")
        super().__init__(value)

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        self.phones = [phone for phone in self.phones if phone.value != phone_number]

    def edit_phone(self, old_phone_number, new_phone_number):
        for phone in self.phones:
            if phone.value == old_phone_number:
                phone.value = new_phone_number

    def add_birthday(self, date):
        if self.birthday is not None:
            raise ValueError("A contact can have one birthday at most.")
        self.birthday = Birthday(date)

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def __str__(self):
        contact_info = f"Contact name: {self.name.value}, phones: {"; ".join(str(p) for p in self.phones)}"
        if self.birthday:
            contact_info += f", birthday: {self.birthday}"
        return contact_info

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def find(self, name):
        return self.data.get(name, None)

    def get_birthdays_per_week(self):
        birthdays_by_day = defaultdict(list)

        today = datetime.today().date()

        for user in self.data.values():
            name = user.name.value
            birthday = user.birthday.value.date()
            birthday_this_year = birthday.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            delta_days = (birthday_this_year - today).days

            if delta_days < 0:
                continue

            day_of_week = (today + timedelta(days=delta_days)).strftime("%A")

            if day_of_week in ["Saturday", "Sunday"]:
                delta_days += 1
                day_of_week = "Monday"

            if 0 <= delta_days < 7:
                birthdays_by_day[day_of_week].append(name)

        for day, names in birthdays_by_day.items():
            print(f"{day}: {", ".join(names)}")
    
    def save_to_file(self, filename):
        data_to_save = {
            "records": {name: {
                "phones": [str(phone) for phone in record.phones],
                "birthday": str(record.birthday) if record.birthday else None
            } for name, record in self.data.items()}
        }

        with open(filename, "w") as file:
            json.dump(data_to_save, file)

    def load_from_file(self, filename):
        try:
            with open(filename, "r") as file:
                data = json.load(file)

            self.data = {}
            for name, record_data in data["records"].items():
                record = Record(name)
                for phone_str in record_data["phones"]:
                    record.add_phone(phone_str)
                if record_data["birthday"]:
                    record.add_birthday(record_data["birthday"])
                self.data[name] = record

        except (FileNotFoundError, json.JSONDecodeError):
            print("Error loading data from file.")

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return "Invalid command. Please use the format: command [name] [phone number]."
        except KeyError as e:
            return "Error: Name not found."
        except IndexError as e:
            return "Index is outside the valid range of indices for that sequence. Try again."
    return inner

@input_error
def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

@input_error
def add_contact(args, contacts):
    name, phone = args
    if name in contacts:
        return f"{name} is already in your phonebook. Try again please."
    else:
        contacts[name] = phone
        return "Contact added."

@input_error
def change_contact(args, contacts):
    name, new_phone = args
    if name in contacts:
        contacts[name] = new_phone
        return "Contact updated."
    else:
        return "Error: Name not found."

@input_error
def show_phone(args, contacts):
    name = args[0]
    if name in contacts:
        return contacts[name]
    else:
        return "Error: Name not found."

@input_error
def show_all(contacts):
    if contacts:
        for name, phone in contacts.items():
            print(f"{name}: {phone}")
    else:
        print("No contacts found.")

@input_error
def add_birthday(args, address_book):
    name, date_of_birth = args
    record = address_book.find(name)
    if record:
        record.add_birthday(date_of_birth)
        return "Birthday added successfully."
    else:
        return "Error: Name not found."

@input_error
def show_birthday(args, address_book):
    name = args[0]
    record = address_book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday: {record.birthday}"
    else:
        return f"Error: {name}'s birthday not found."

@input_error
def list_birthdays(address_book):
    if not address_book:
        print("No birthdays found next week.")
    else:
        address_book.get_birthdays_per_week()

@input_error
def main():
    address_book = AddressBook()
    filename = "address_book.json"
    try:
        address_book.load_from_file(filename)
        print("Address book loaded successfully.")
    except FileNotFoundError:
        print("No existing address book found. Starting with an empty address book.")

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)
        if command in ["close", "exit", "goodbye"]:
            print("Goodbye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            name, phone = args
            record = Record(name)
            record.add_phone(phone)
            address_book.add_record(record)
            print("Contact added.")
        elif command == "change":
            name, new_phone = args
            record = address_book.find(name)
            if record:
                record.edit_phone(record.phones[0].value, new_phone)
                print("Contact updated.")
            else:
                print("Error: Name not found.")
        elif command == "phone":
            print(show_phone(args, address_book.data))
        elif command == "all":
            show_all(address_book.data)
        elif command == "add-birthday":
            print(add_birthday(args, address_book))
        elif command == "show-birthday":
            print(show_birthday(args, address_book))
        elif command == "birthdays":
            list_birthdays(address_book)
        elif command == "save":
            address_book.save_to_file(filename)
            print("Address book saved.")
        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()