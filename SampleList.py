fruits  = ["apple", "banana","mango"]

print ("Current Fruit List:", fruits)

new_fruit = input("Enter fruit: ")
fruits.append(new_fruit)

remove_fruit = input ("Remove fruit: ")
if remove_fruit in fruits:
    fruits.remove(remove_fruit)
    print(f"{remove_fruit} removed.")
else:
    print(f"{remove_fruit} not found in list.")

print ("Fruit List:", fruits)
