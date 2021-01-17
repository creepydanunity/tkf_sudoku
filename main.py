import csv


picked = False
with open('new.csv', encoding="utf8") as csv_file:
    reader = csv.reader(csv_file, delimiter=',')
    all_info = [list(map(int, i[1:3])) + [float(i[3])] for index, i in enumerate(reader) if index > 0][1:]
    maximum_profit = 0
    buy_info, sell_info, temp_list = [], [], []
    counter = 0
    temp_max = max([i[2] for i in all_info[1:]])
    for index in range(len(all_info) - 1):
        #print(index)
        if all_info[index][2] == temp_max:
            temp_list = [i[2] for i in all_info[index + 1:]]
            counter = index + 1
            if temp_list:
                temp_max = max(temp_list)
            else:
                break
        if temp_max - all_info[index][2] > maximum_profit:
            #print(temp_list)
            #sell_info = all_info[temp_list.index(temp_max)]
            #print(temp_max, temp_list)
            maximum_profit = temp_max - all_info[index][2]
            buy_info = all_info[index]

    print(buy_info, sell_info, maximum_profit)