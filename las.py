import time
from random import choices
import string


class User:
    def __init__(self, name, user_type, is_graduate=False):
        self.name = name
        self.user_type = user_type  # "Student," "Faculty," or "Staff"
        self.is_graduate = is_graduate
        self.library_card = None
        self.borrowed_books = []

        if is_graduate:
            self.library_card = self.SmartCard()
            self.library_card.activate_membership()

    def can_borrow(self):
        if self.user_type == "Graduate" and not self.library_card.is_valid_membership():
            return False
        return len(self.borrowed_books) < self.get_max_books_borrowed()

    def get_max_books_borrowed(self):
        if self.user_type == "Faculty":
            return 5
        return 3

    def get_max_borrowing_days(self):
        if self.user_type == "Faculty":
            return 30
        return 15

    class SmartCard:
        def __init__(self):
            self.membership_valid = False
            self.pin = None

        def activate_membership(self):
            self.membership_valid = True
            self.pin = ''.join(choices(string.digits, k=4))  # Generate a PIN

        def is_valid_membership(self):
            return self.membership_valid

    class Kiosk:
        def __init__(self, las):
            self.las = las

        def search_book(self, title):
            return self.las.search_book(title)

        def reserve_book(self, user, title):
            return self.las.reserve_book(user, title)

        def borrow_book(self, user, title, pin, days=15):
            if user.can_borrow():
                if self.las.validate_pin(user, pin):
                    result = self.las.lend_book(user, title, days)
                    return f"Borrowing through Kiosk: {result}"
                else:
                    return "Invalid PIN code."
            return "Graduates cannot borrow books from Kiosks."

        def extend_due_date(self, user, title, pin, days=15):
            if user.can_borrow():
                if self.las.validate_pin(user, pin):
                    result = self.las.extend_due_date(user, title, days)
                    return f"Extension via Kiosk: {result}"
                else:
                    return "Invalid PIN code."
            return "Graduates cannot extend due dates via Kiosks."

        def send_reservation_email(self, user, title):
            # In a real implementation, you would send an email to the user.
            # For the sake of this example, we print a message.

            print(f"Email notification sent to {user.name}: Your reserved book '{title}' has arrived.")


class Book:
    def __init__(self, title, author, publication_year, is_textbook=False):
        self.title = title
        self.author = author
        self.publication_year = publication_year
        self.is_textbook = is_textbook
        self.due_date = None
        self.extension_attempts = 0


class Periodical:
    def __init__(self, title, issue_number, publication_year):
        self.title = title
        self.issue_number = issue_number
        self.publication_year = publication_year


class LibraryAutomationSystem:
    def __init__(self):
        self.books = []
        self.periodicals = []
        self.users = []
        self.reserved_books = {}

    def add_book(self, title, author, publication_year, is_textbook=False):
        book = Book(title, author, publication_year, is_textbook)
        self.books.append(book)

    def add_periodical(self, title, issue_number, publication_year):
        periodical = Periodical(title, issue_number, publication_year)
        self.periodicals.append(periodical)

    def search_book(self, title):
        return [book for book in self.books if title in book.title]

    def search_periodical(self, title):
        return [periodical for periodical in self.periodicals if title in periodical.title]

    def add_user(self, name, user_type, is_graduate=False):
        new_user = User(name, user_type, is_graduate)
        if new_user.is_graduate:
            new_user.library_card.activate_membership()
            self.users.append(new_user)
            return new_user

    def validate_pin(self, user, pin):
        return user.library_card and user.library_card.pin == pin

    def lend_book(self, user, title, days=15):
        # Check if the user can borrow more books
        if not user.can_borrow():
            return "Borrowing limit has reached."

        # Get the current time
        current_time = time.time()

        # Find the book and check the borrowing conditions
        for book in self.books:
            if book.title == title:
                if book.is_textbook and user.user_type != "Faculty":
                    return "Only faculty members can borrow textbooks."

                if user.user_type == "Faculty" and book.is_textbook:
                    days = min(days, 180)  # Special rule for faculty borrowing textbooks

                max_borrowing_days = user.get_max_borrowing_days()
                if days <= max_borrowing_days:
                    user.borrowed_books.append(book)  # Append the book to the user's borrowed books
                    book.due_date = current_time + days * 24 * 3600  # Set the due date
                    return f"Lent book: {title} for {days} days."
                else:
                    return f"Cannot borrow for more than {max_borrowing_days} days."
            # This else belongs to the if statement checking the book title
            # If no book is found with the given title, the loop ends and this message is displayed
        return "Book not available for lending or already reserved."

    def reserve_book(self, new_user, title):
        if new_user.user_type == "Faculty":
            for book in self.books:
                if book.title == title and not book.is_textbook:
                    return f"Book reserved: {title}"
            return "Book not available for reservation or already reserved."
        return "Faculty members can reserve textbooks only."

    def extend_due_date(self, new_user, title, days=15):
        if new_user.can_borrow():
            for book in new_user.books_borrowed:
                if book.title == title:
                    if book.due_date is not None:
                        if book.due_date > time.time():
                            if self.can_extend_book(book, new_user):
                                fine = self.calculate_fine(book.due_date, time.time(), days)
                                book.due_date += days * 24 * 3600
                                book.extension_attempts += 1
                                return f"Extended due date for book: {title} for {days} days. Fine: {fine} TL"
                            else:
                                return "Maximum extension attempts reached for this book."
                        else:
                            return "Extension is not possible after the due date has passed."
                    return "The book was not borrowed or has an indefinite due date."
            return "Book not found in your borrowed books."
        return "Graduates cannot extend due dates."

    def extend_due_date_at_counter(self, user, title, days=15):
        for book in user.books_borrowed:
            if book.title == title and book.extension_attempts < 3:
                if book.due_date and book.due_date > time.time():
                    book.due_date += days * 24 * 3600
                    book.extension_attempts += 1
                    return f"Due date extended at counter for {title} by {days} days."
                return "Cannot extend. Either due date has passed or indefinite due date."
            return "Book not found or maximum extensions reached."
        return "No such book borrowed by user."

    def can_extend_book(self, book, new_user):
        return book.extension_attempts < 3

    def calculate_fine(self, due_date, return_time, days):
        time_difference = return_time - due_date
        if time_difference <= 0:
            return 0  # No fine if returned on or before the due date
        elif time_difference <= 7 * 24 * 3600:
            return 10  # Fine for the first week of overdue
        else:
            # Calculate fine for subsequent weeks (20 TL per week)
            weeks_overdue = int(time_difference / (7 * 24 * 3600))
            return 10 + (weeks_overdue - 1) * 20

    def check_reserved_books(self):
        current_time = time.time()
        books_to_cancel = []
        for title, (user, reservation_time) in self.reserved_books.items():
            if current_time - reservation_time >= 2 * 24 * 3600:  # 2 days
                books_to_cancel.append(title)
        for title in books_to_cancel:
            del self.reserved_books[title]


class CounterService:
    def __init__(self, las):
        self.las = las

    def borrow_book(self, user, title, days=15):
        current_time = time.time()
        if not user.can_borrow():
            return "Borrowing limit reached at the counter."

        max_borrowing_days = user.get_max_borrowing_days()
        for book in self.las.books:
            if book.title == title and (not book.is_textbook or user.user_type == "Faculty"):
                if days <= max_borrowing_days:
                    user.books_borrowed.append(book)
                    # Set the due date for the book
                    book.due_date = current_time + days * 24 * 3600
                    return f"Book borrowed from counter: {title} for {days} days."
                else:
                    return f"Cannot borrow for more than {max_borrowing_days} days from the counter."
            else:
                return "Book not available for borrowing or already reserved at the counter."


class WebInterface:
    def __init__(self, las):
        self.las = las

    def search_book(self, title):
        return self.las.search_book(title)

    def reserve_book(self, new_user, title):
        result = self.las.reserve_book(new_user, title)
        if result.startswith("Book reserved:"):
            self.send_reservation_email(new_user, title)
            return result

    def extend_due_date(self, new_user, title, pin, days=15):
        if new_user.can_borrow():
            if self.las.validate_pin(new_user, pin):
                result = self.las.extend_due_date(new_user, title, days)
                return f"Extension via web: {result}"
            else:
                return "Invalid PIN code."
        else:
            return "Graduates cannot extend due dates via the web."

    def send_reservation_email(self, new_user, title):
        # In a real implementation, you would send an email to the user.
        # For the sake of this example, we print a message.
        print(f"Email notification sent to {new_user.name}: Your reserved book '{title}' has arrived.")


las = LibraryAutomationSystem()
counter_service = CounterService(las)

name = input("Enter your name: ")
user_type = input("Enter your user type (Student, Faculty, Staff): ")

if user_type.lower() == "student":
    is_graduate = input("Are you a graduate? (yes or no): ").lower() == "yes"
else:
    is_graduate = False

# Add the user to the system
new_user = las.add_user(name, user_type, is_graduate)

if new_user:
    print(f"User added to the system. Your pin is {new_user.library_card.pin if new_user.library_card else 'N/A'}")
    if is_graduate:
        annual_fee = input("There is an annual fee for graduate students. Would you like to proceed? (yes or no):")
        if annual_fee.lower() == "yes":
            new_user.library_card.activate_membership()
            print(f"User added to the system. Your PIN is {new_user.library_card.pin}")
        else:
            print("You cannot access the library system.")
    else:
        print("No user was added to the system.")

if not is_graduate:
    pin = input("Please enter your pin number:")
    if len(pin) != 4:
        pin = input("Please enter a valid pin number:")

title_to_search = input("Enter the title of the book you want to search for: ")
search_results = las.search_book(title_to_search)

if search_results:
    print(f"Found {len(search_results)} book(s) matching the title '{title_to_search}'.")
    # Display book details here (optional)

    print("Select an option:")
    print("1. Borrow a book")
    print("2. Reserve a book")
    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        # Borrow book logic
        days = input("Enter number of days you want to borrow the book for: ")
        result = las.lend_book(new_user, title_to_search, int(days))
        print(result)
    elif choice == '2':
        # Reserve book logic
        result = las.reserve_book(new_user, title_to_search)
        print(result)
else:
    print("No books found with that title. Please try again.")
