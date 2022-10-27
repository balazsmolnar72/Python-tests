import matplotlib.pyplot as plt
"""   
# x axis values
x = [1,2,3]
# corresponding y axis values
y = [2,4,1]
  
# plotting the points 
plt.plot(x, y)
  
# naming the x axis
plt.xlabel('x - axis')
# naming the y axis
plt.ylabel('y - axis')
  
# giving a title to my graph
plt.title('My first graph!')
  
# function to show the plot
plt.savefig('myfig')
plt.show()
 """

""" #Bar chart

# x-coordinates of left sides of bars
left = [1, 2, 3, 4, 5]

# heights of bars
height = [10, 24, 36, 40, 5]

# labels for bars
tick_label = ['one', 'two', 'three', 'four', 'five']

fig, ax=plt.subplots()

# plotting a bar chart
ax.bar(left, height, tick_label = tick_label,
		width = 0.8, color = ['red', 'green'], label='alma')
ax.bar(left, height, tick_label = tick_label,
		width = 0.8, color = ['red', 'green'],label='korte')

#adding also line
# x axis values
x = [1,2,3]
# corresponding y axis values
y = [10,24,36]
  
# plotting the points 
plt.plot(x, y)

# naming the x-axis
plt.xlabel('x - axis')
# naming the y-axis
plt.ylabel('y - axis')
# plot title
plt.title('My bar chart!')

# function to show the plot
plt.show() """

import matplotlib.pyplot as plt


Scenarios = ['On Premise', 'Exadata', 'ExaCC', 'ExaCC BYOL', 'OCI DBCS']
Infrastructure = [80000, 100000, 90000, 90000, 40000]
License_support = [340000, 280000, 0, 200000, 0]
Universal_credits=[0,0,89000,25000,45000]
width = 0.9       # the width of the bars: can also be len(x) sequence

Totals=list(map(lambda a,b,c: a+b+c, Infrastructure, License_support,Universal_credits))

def cm_to_inch(value):
    return value/2.54

#plt.figure(figsize=(cm_to_inch(12),cm_to_inch(5)))

fig, ax = plt.subplots()
fig.set_size_inches(cm_to_inch(30),cm_to_inch(10),forward=True)

bar1=ax.bar(Scenarios, Infrastructure, width, label='Infrastructure')
bar2=ax.bar(Scenarios, License_support, width, bottom=Infrastructure,label='License support')
bottomList = list(map(lambda a,b: a+b, Infrastructure, License_support))
bar3=ax.bar(Scenarios, Universal_credits, width, bottom=bottomList,label='Universal credits')

Infra_labels=map(lambda val: 'Infra \n${:,.0f}K'.format(val/1000) if(val>0) else "",Infrastructure)
ax.bar_label(bar1,labels=Infra_labels,label_type='center',fontsize=8,color='w')
License_support_labels=map(lambda val: 'DB Support \n${:,.0f}K'.format(val/1000) if(val>0) else "",License_support)
ax.bar_label(bar2,labels=License_support_labels,label_type='center',fontsize=8)
Universal_credits_labels=map(lambda val: 'UC \n${:,.0f}K'.format(val/1000,0) if(val>30000) 
	else ('UC ${:,.0f}K'.format(val/1000,0) if(val>0) 
	else ""),Universal_credits)
ax.bar_label(bar3,labels=Universal_credits_labels,label_type='center',fontsize=8)

Total_labels=map(lambda val: 'Savings \n{:.0%}\nTotal \n${:,.0f}K'.format(val/Totals[0]-1,val/1000) if(val!=Totals[0]) 
	else ('Total \n${:,.0f}K'.format(val/1000) if (val>0) else ""),Totals)
ax.bar_label(bar3,label_type='edge',labels=Total_labels,padding=5,fontsize=10)

#adding also line
# x axis values
#x = [1,2,3]
# corresponding y axis values
#y = list(map(lambda a,b: a+b, men_means, women_means))

# if I want to add total to the custom list as a label
#y_labels=map(lambda str: 'total {}'.format(str),y)
#ax.bar_label(bar2,labels=y_labels,fmt='total %g')



  
# plotting the points 
#plt.plot(labels, y)


ax.set_ylabel('Cost in USD')
ax.set_title('4 years TCO of the different scenarios')
ax.legend(fontsize=10)
plt.ylim(top = max(Totals)*1.3)


#fig.subplots_adjust(top=0.8)
fig.tight_layout()

plt.show()

