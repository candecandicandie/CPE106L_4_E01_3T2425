# stats.py

def mean(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def median(numbers):
    if not numbers:
        return 0
    numbers = sorted(numbers)
    n = len(numbers)
    mid = n // 2
    if n % 2 == 0:
        return (numbers[mid - 1] + numbers[mid]) / 2
    else:
        return numbers[mid]

def mode(numbers):
    if not numbers:
        return 0
    freq = {}
    for num in numbers:
        freq[num] = freq.get(num, 0) + 1
    max_freq = max(freq.values())
    modes = [k for k, v in freq.items() if v == max_freq]
    if len(modes) == len(freq):
        return 0  # No mode
    return modes[0] if len(modes) == 1 else modes

def main():
    try:
        user_input = input("Enter a list of numbers separated by spaces: ")
        numbers = list(map(float, user_input.strip().split()))
    except ValueError:
        print("Invalid input. Please enter numbers only.")
        return

    print(f"Mean: {mean(numbers)}")
    print(f"Median:1  {median(numbers)}")
    print(f"Mode: {mode(numbers)}")

if __name__ == "__main__":
    main()
