"""
File: student.py
Resources to manage a student's name and test scores.
"""

import random

class Student(object):
    """Represents a student."""

    def __init__(self, name, number):
        """All scores are initially 0."""
        self.name = name
        self.scores = [0] * number

    def getName(self):
        """Returns the student's name."""
        return self.name

    def setScore(self, i, score):
        """Resets the ith score, counting from 1."""
        self.scores[i - 1] = score

    def getScore(self, i):
        """Returns the ith score, counting from 1."""
        return self.scores[i - 1]

    def getAverageScore(self):
        """Returns the average score."""
        return sum(self.scores) / len(self.scores)

    def getHighScore(self):
        """Returns the highest score."""
        return max(self.scores)

    def __str__(self):
        """Returns the string representation of the student."""
        return "Name: " + self.name + "\nScores: " + " ".join(map(str, self.scores))

    # Comparison methods
    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __ge__(self, other):
        return self.name >= other.name

def main():
    # Create multiple Student objects
    s1 = Student("Lui", 3)
    s2 = Student("Kyle", 3)
    s3 = Student("Matt", 3)
    s4 = Student("Elijah", 3)
    s5 = Student("Kurt", 3)

    # Set sample scores
    for s in [s1, s2, s3, s4, s5]:
        for i in range(1, 4):
            s.setScore(iSS, random.randint(70, 100))

    # Place them into a list
    students = [s1, s2, s3, s4, s5]

    # Shuffle the list
    print("Shuffled list:")
    random.shuffle(students)
    for student in students:
        print(student)
        print()

    # Sort the list
    print("Sorted list by name:")
    students.sort()
    for student in students:
        print(student)
        print()

if __name__ == "__main__":
    main()
