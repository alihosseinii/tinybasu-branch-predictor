      lui  rx0, 0        # rx0 = 0
      li   rx1, 1        # rx1 = result = 1
      li   rx2, 1        # rx2 = i = 1
      addi rx3, rx0, 31  # rx3 = 31
      addi rx3, rx3, 19  # rx3 = 50
      addi rx7, rx3, 1   # rx7 = n + 1 = 51 

outer: addi rx4, rx0, 0   # rx4 = temp = 0
       li   rx5, 1        # rx5 = j = 1
       addi rx6, rx2, 1   # rx6 = i + 1 

inner: add  rx4, rx4, rx1 # temp += result
       addi rx5, rx5, 1   # j++
       bne  rx5, rx6, inner # if j != i+1 go to inner

       addi rx1, rx4, 0   # result = temp
       addi rx2, rx2, 1   # i++
       bne  rx2, rx7, outer # if i != 51 go to outer
