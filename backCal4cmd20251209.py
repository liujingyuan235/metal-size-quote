
import os
import json
import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
import argparse
import array
import copy

# import requests

# 设置刀口厚度
kerf = 5
# 设置废料尺寸
tresh = 50

# 设置切割模式 1-竖切 2-横切
cut_mode = 1
# 设置排序优先类型 1-废料最小优先 2-余料最大优先 3-余料最少优先
priority = 1
#废料是否吞并 1-废料保留 2-合并余料后吞并废料 3-吞并废料后合并余料
left_merge = 1
#材料厚度
sizethick = 20
#材料密度（g/cm³），默认按铝材近似值保持旧版行为
material_density = 2.8
#设置用料排序优化门限值
useRate = 0.75
msg = "正常运行结束"
# 存储用户选择的输出文件夹路径
output_folder = ""


# 定义矩形类
class Rectangle:    
    def __init__(self, width, height, direction=0, num=1, id=None, producer="", orderNo=None):
        self.width = width  # 矩形宽度
        self.height = height  # 矩形高度
        self.direction = direction
        self.num = num
        self.id = id
        self.producer = producer
        # 若未传入orderNo，默认赋值为[1]
        if orderNo is None:
            self.orderNo = [1]
        else:
            # 可选：校验传入的orderNo是否为非空列表（避免空列表）
            if not isinstance(orderNo, list):
                raise TypeError("orderNo must be a list")
            if len(orderNo) == 0:
                raise ValueError("orderNo cannot be an empty list")
            self.orderNo = orderNo

def backPack(n,m,v,s,sel):
    #多重背包
    f = [[0] * (m+1) for _ in range(n+1)]
    for i in range(1,n+1):
        for j in range(0,m+1):
            f[i][j]=f[i-1][j]  
            for k in range(1,s[i-1]+1):
                if j>=v[i-1]*k:
                    f[i][j]=max(f[i][j],f[i-1][j-v[i-1]*k]+v[i-1]*k)
    #print(f)

    cap=m    
    for i in range(n,0,-1):    
        for j in range(cap,0,-1):        
            for k in range(s[i-1],0,-1):
                if(j>=v[i-1]*k):
                    if(f[i][j]==f[i-1][j-v[i-1]*k]+v[i-1]*k):
                        cap-=v[i-1]*k
                        #print('pick:',i-1,'vol:',v[i-1],'num:',k,'weight',v[i-1])
                        sel.append([i-1,k])
                        break        
            break
    #print(f[n][m])
    #print(sel)


def can_placed(i,remaining_rects,current_width,current_height,hgtcnt,sel,key):    
    global style,group_combine
    if style==1:
        width=remaining_rects[i][0].width
    else:
        width=remaining_rects[i][0].height
            
    col = int((current_width+kerf) / (width+kerf))

##    print(col)

    if group_combine == 2 and col>1:    
        col=1

    height=[]
    cnt=[]    
    for j in range(len(remaining_rects[i])):
        rect=remaining_rects[i][j];
        if style==1:
            if rect.height<=current_height and (rect.direction==0 or rect.direction==key):
                height.append(rect.height)
                cnt.append(rect.num)
        else:            
            if rect.width<=current_height and (rect.direction==0 or rect.direction!=key):
                height.append(rect.width)
                cnt.append(rect.num)    

    if not(col and height):        
        area=0
        maxleft=0
        return False,col,area,maxleft    
    
    col=min(max(cnt),col)
    flag=1
    num=remaining_rects[i][0].num
    for j in range(len(remaining_rects[i])):
        rect=remaining_rects[i][j];
        if style==1:
            if rect.height<=current_height and rect.num>=col and (rect.direction==0 or rect.direction==key):                
                hgtcnt.append([rect.height+kerf,int(rect.num/col),j])
        else:        
            if rect.width<=current_height and rect.num>=col and (rect.direction==0 or rect.direction!=key):                
                hgtcnt.append([rect.width+kerf,int(rect.num/col),j])

        if rect.num != num:
            flag=0

    hgtcnt.sort(key=lambda r: r[0])  #高度升序排序

    n=len(hgtcnt)
    altitude = 0
    for m in range(n):  #个数相同且总高度不超界时特殊处理             
        altitude += hgtcnt[m][0]
    row = int((current_height+kerf) / altitude)
    
    mat=[]
    if flag:
        for p in range(row,1,-1):
            for q in range(2,col+1):
                if p*q <= num:
                   mat.append([p,q,p*q])
               
    if mat:        
        mat.sort(key=lambda r: -r[2])        
        #更新row和col
        row=mat[0][0]
        col=mat[0][1]
        a=(width+kerf)*col-kerf
        b=altitude*row-kerf
        if key==1:
            maxleft=max([(current_width-a-kerf)*current_height,(current_height-b-kerf)*a])
        else:
            maxleft=max([(current_height-b-kerf)*current_width,(current_width-a-kerf)*b])

        if len(mat)>1 and mat[0][2]==mat[1][2]:           
            a=(width+kerf)*mat[1][1]-kerf
            b=altitude*mat[1][0]-kerf
            if key==1:
                maxleft2=max([(current_width-a-kerf)*current_height,(current_height-b-kerf)*a])
            else:
                maxleft2=max([(current_height-b-kerf)*current_width,(current_width-a-kerf)*b])
            if maxleft<maxleft2:
                row=mat[1][0]
                col=mat[1][1]
                maxleft=maxleft2
        
        for m in range(n):
            sel.append([m,row])

        area=width*(altitude-kerf)*row*col        
            
    else:
        volume=array.array('i',[])
        count=[]    
        for j in range(n):                
            volume.append(int(hgtcnt[j][0]))
            count.append(hgtcnt[j][1])

        backPack(n,int(current_height+kerf),volume,count,sel)            

        disp=0
        area=0
        for k in range(len(sel)):
            j=hgtcnt[sel[k][0]][2]  
            for m in range(sel[k][1]):
                if style==1:
                    disp+=remaining_rects[i][j].height+kerf
                    area+=width*remaining_rects[i][j].height*col
                else:
                    disp+=remaining_rects[i][j].width+kerf
                    area+=width*remaining_rects[i][j].width*col

        a=(width+kerf)*col-kerf
        b=disp-kerf 
        if key==1:
            maxleft=max([(current_width-a-kerf)*current_height,(current_height-b-kerf)*a])
        else:
            maxleft=max([(current_height-b-kerf)*current_width,(current_width-a-kerf)*b])
            

    #print('area:',area,'maxleft:',maxleft)
    return True,col,area,maxleft
        

def place_rectangles_vertically(x_start, y_start, big_rect, current_rect, remaining_rects, placed_rectangles, part, leftover_rects):
    global style,xstart_list,ystart_list
    layer = len(x_start) - 1
    if layer < 0:
        return remaining_rects

    if x_start[layer] >= big_rect.width and y_start[layer] < big_rect.height:
        x_start[layer]-=kerf
        current_rect.width+=kerf
    elif x_start[layer] < big_rect.width and y_start[layer] >= big_rect.height:
        y_start[layer]-=kerf
        current_rect.height+=kerf 

    if remaining_rects:

        #print('len:',len(remaining_rects))    
        
        # if style==1:
        #     remaining_rects.sort(key=lambda r: (r[0].producer == "", -r[0].width))  #空字符串排在后面 # Sort by width 
        # else:
        #     remaining_rects.sort(key=lambda r: (r[0].producer == "", -r[0].height)) #空字符串排在后面 # Sort by height      
        
        remaining_rects.sort(key=lambda r: -r[0].width*r[0].height)  # Sort by first single area   
        # remaining_rects.sort(key=lambda r: -r[0].width*r[0].height*r[0].num)  # Sort by first total area        
        # remaining_rects.sort(key=lambda r: -sum(r[i].width*r[i].height*r[i].num for i in range(len(r))))  # Sort by total area

        #for i in range(len(remaining_rects)):
        #    for j in range(len(remaining_rects[i])):                    
        #        rect=remaining_rects[i][j]
        #        print([i,j],[rect.width,rect.height,rect.direction,rect.num])
        #    print('\n')  

        longest_rect = None        
        for i in range(len(remaining_rects)):         

            
            
            hgtcnt1=[]
            sel1=[]
            hgtcnt2=[]
            sel2=[]
            canplace1,col1,area1,maxleft1 = can_placed(i,remaining_rects,current_rect.width,current_rect.height,hgtcnt1,sel1,1)
            canplace2,col2,area2,maxleft2 = can_placed(i,remaining_rects,current_rect.height,current_rect.width,hgtcnt2,sel2,2)            
            
            transpose = 0
            if not canplace1 and  not canplace2:
                continue 
            elif canplace1 and not canplace2:
                transpose = 0
            elif not canplace1 and canplace2:
                transpose = 1
            elif area1 > area2:
                transpose = 0
            elif area1 < area2:
                transpose = 1
            elif maxleft1 > maxleft2:
                transpose = 0
            elif maxleft1 < maxleft2:
                transpose = 1
            else:
                transpose = 0

            #print('transpose:',transpose)  

##            transpose=0
##            print('transpose:',transpose)  

            delist=[]
            disp=0
            col=0
            if transpose == 0: 
                for k in range(len(sel1)):
                    j=hgtcnt1[sel1[k][0]][2]
                    delist.append(j)
                    row=sel1[k][1]
                    col=col1
                    rect=remaining_rects[i][j]   
                    
                    for m in range(row):
                        if style==1:
                            for n in range(col):                                
                                placed_rectangles.append({'rect': Rectangle(rect.width,rect.height, rect.direction, 1, rect.id, rect.producer, [rect.orderNo[0]]), 'x': x_start[layer]+n*(rect.width+kerf), 'y': y_start[layer]+disp, 'rotated': False})
                                del rect.orderNo[0]
                            disp+=rect.height+kerf
                        else:
                            for n in range(col):                        
                                placed_rectangles.append({'rect': Rectangle(rect.height,rect.width, rect.direction, 1, rect.id, rect.producer, [rect.orderNo[0]]), 'x': x_start[layer]+n*(rect.height+kerf), 'y': y_start[layer]+disp, 'rotated': True})
                                del rect.orderNo[0]
                            disp+=rect.width+kerf 
                            
                    if rect.num-row*col > 0:                      
                        remaining_rects[i].append(Rectangle(rect.width, rect.height,rect.direction,rect.num-row*col,rect.id, rect.producer, rect.orderNo))
                        
                if style==1:
                    longest_rect=Rectangle(rect.width*col+kerf*(col-1),disp-kerf)
                else:
                    longest_rect=Rectangle(rect.height*col+kerf*(col-1),disp-kerf)
            else:
                for k in range(len(sel2)):
                    j=hgtcnt2[sel2[k][0]][2]
                    delist.append(j)
                    row=sel2[k][1]
                    col=col2
                    rect=remaining_rects[i][j]   
                    
                    for n in range(row):
                        if style==1:
                            for m in range(col):                                              
                                placed_rectangles.append({'rect': Rectangle(rect.height,rect.width, rect.direction, 1, rect.id, rect.producer, [rect.orderNo[0]]), 'x': x_start[layer]+disp, 'y': y_start[layer]+m*(rect.width+kerf), 'rotated': True})
                                del rect.orderNo[0]
                            disp+=rect.height+kerf
                        else:
                            for m in range(col):                                              
                                placed_rectangles.append({'rect': Rectangle(rect.width,rect.height, rect.direction, 1, rect.id, rect.producer, [rect.orderNo[0]]), 'x': x_start[layer]+disp, 'y': y_start[layer]+m*(rect.height+kerf), 'rotated': False})
                                del rect.orderNo[0]
                            disp+=rect.width+kerf  
                            
                    if rect.num-row*col > 0:                      
                        remaining_rects[i].append(Rectangle(rect.width, rect.height,rect.direction,rect.num-row*col,rect.id, rect.producer, rect.orderNo))
                        
                if style==1:
                    longest_rect=Rectangle(disp-kerf,rect.width*col+kerf*(col-1))  
                else:
                    longest_rect=Rectangle(disp-kerf,rect.height*col+kerf*(col-1))  
            delist.sort(reverse=True) #j按降序排序
            for j in delist:                
                del remaining_rects[i][j]            

            if(len(remaining_rects[i])==0):
                del remaining_rects[i]  
            
            #placed_rectangles.append({'rect': longest_rect, 'x': x_start[layer], 'y': y_start[layer], 'rotated': False})          
            break       
        
        if longest_rect is None:
            if current_rect.width > 0 and current_rect.height > 0:
                leftover_rects.append({'x': x_start[layer], 'y': y_start[layer], 'width': current_rect.width, 'height': current_rect.height})
                #print("余料 len:", len(x_start), "layer:", layer, [x_start[layer], y_start[layer]], [current_rect.width, current_rect.height])
            if part == 1:
                x_val = x_start[layer]
                for i in range(layer, -1, -2):
                    if x_start[i] == x_val:
                        del x_start[i]
                        del y_start[i]
            else:
                del x_start[layer]
                del y_start[layer]

            return remaining_rects
        
        x_start.append(x_start[layer] + longest_rect.width + kerf)
        y_start.append(y_start[layer]) 
        xstart_list.append(x_start[layer] + longest_rect.width)
        ystart_list.append(y_start[layer])           

        x_start.append(x_start[layer])
        y_start.append(y_start[layer] + longest_rect.height + kerf)
        xstart_list.append(x_start[layer])
        ystart_list.append(y_start[layer] + longest_rect.height)

        current_rect_1 = Rectangle(longest_rect.width, current_rect.height - (longest_rect.height + kerf))
        remaining_rects = place_rectangles_vertically(x_start, y_start, big_rect, current_rect_1, remaining_rects, placed_rectangles, 1, leftover_rects)

        current_rect_2 = Rectangle(current_rect.width - (longest_rect.width + kerf), current_rect.height)
        remaining_rects = place_rectangles_vertically(x_start, y_start, big_rect, current_rect_2, remaining_rects, placed_rectangles, 2, leftover_rects)
      
    else:        
        # 在没有剩余小矩形时，继续递归查找大矩形剩余部分
        if current_rect.width > 0 and current_rect.height > 0:
            leftover_rects.append({'x': x_start[layer], 'y': y_start[layer], 'width': current_rect.width, 'height': current_rect.height})
        if part == 1:
            x_val = x_start[layer]
            for i in range(layer, -1, -2):
                if x_start[i] == x_val:
                    del x_start[i]
                    del y_start[i]
        else:
            del x_start[layer]
            del y_start[layer]        

    return remaining_rects

def pack_rectangles(big_rect, remaining_rects):
    global cut_mode,style,group_combine,priority,xstart_list,ystart_list

    remaining_rects.sort(key=lambda r: -r.width*r.height)  # Sort by first single area 
    if cut_mode == 2:
        #交换大矩形和小矩形的长和宽,direction无需变化
        big_rect = Rectangle(big_rect.height,big_rect.width,big_rect.direction,big_rect.num,big_rect.id,big_rect.producer)
        remaining_rects = [Rectangle(rect.height,rect.width,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo) for rect in remaining_rects]      

    selection = []        
    placed_rectangles_cycle = []
    leftover_cycle = []
    remainings_cycle = []
    xtick_cycle = []
    ytick_cycle = []
    idx=0
    for cycle in range(4):

        if cycle==0:
            style=1
            group_combine=1
        elif cycle==1:
            style=2
            group_combine=1
        elif cycle==2:
            style=1
            group_combine=2
        elif cycle==3:
            style=2
            group_combine=2            
        
        #print("style:",style,"group_combine",group_combine)

        remaining4cycle=copy.deepcopy(remaining_rects)           
        
        remainings=[]
        unmatch_rects=[]
        if style==1:
            for rect in remaining4cycle:
                if rect.producer != "" and rect.producer != big_rect.producer:  #不满足厂家匹配需求
                    unmatch_rects.append(rect)
                    continue 
                    
                flag=0
                for i in range(len(remainings)):  
                    if rect.width == remainings[i][0].width and rect.producer == remainings[i][0].producer:
                        remainings[i].append(Rectangle(rect.width, rect.height,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo))
                        flag=1
                if flag==0:
                    remainings.append([Rectangle(rect.width, rect.height,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo)])
        else:
            for rect in remaining4cycle: 
                if rect.producer != "" and rect.producer != big_rect.producer:  #不满足厂家匹配需求
                    unmatch_rects.append(rect)
                    continue  

                flag=0
                for i in range(len(remainings)):  
                    if rect.height == remainings[i][0].height and rect.producer == remainings[i][0].producer:
                        remainings[i].append(Rectangle(rect.width,rect.height,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo))
                        flag=1
                if flag==0:                        
                    remainings.append([Rectangle(rect.width,rect.height,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo)])
        
        #for i in range(len(remainings)):
        #    for j in range(len(remainings[i])):                    
        #        rect=remainings[i][j]
        #        print([i,j],[rect.width,rect.height,rect.direction,rect.num])
        #    print('\n')     
        
        placed_rectangles = []
        leftover_rects = []  # 当前大矩形的余料数组
        final_leftovers = []
        x_start = [0]
        y_start = [0]
        xstart_list = [0]
        ystart_list = [0] 
        remainings = place_rectangles_vertically(x_start, y_start, big_rect, big_rect, remainings, placed_rectangles, 1, leftover_rects)
        if not remainings:
            # 没有剩余小矩形时，继续递归查找大矩形剩余部分
            place_rectangles_vertically(x_start, y_start, big_rect, big_rect, [], placed_rectangles, 1, leftover_rects)

        if left_merge == 1 or left_merge == 2:  # 合并余料
            final_leftovers = merge_leftovers(leftover_rects, big_rect)
        else:
            final_leftovers = leftover_rects
                                
        if left_merge > 1:  # 吞并废料
            check_and_merge_small_pieces(placed_rectangles, final_leftovers)
                    
        if left_merge == 3:
            final_leftovers = merge_leftovers(final_leftovers, big_rect)
            
        utilization,waste_rate,maxleft,left_num,loss_rate=calculate_statistics(big_rect, placed_rectangles, final_leftovers)            
        #print("||utilization",utilization,"waste_rate",waste_rate,"maxleft:",maxleft,"left_num:",left_num,"loss_rate",loss_rate)

        xtick, ytick = get_xyticks(xstart_list,ystart_list)
        xtick_cycle.append(xtick)
        ytick_cycle.append(ytick)
        
        selection.append([idx,utilization,waste_rate,maxleft,left_num,loss_rate,len(placed_rectangles)])            
        placed_rectangles_cycle.append(placed_rectangles)
        leftover_cycle.append(final_leftovers)
        idx+=1         

        remaining4cycle=unmatch_rects            
        for i in range(len(remainings)):
            for j in range(len(remainings[i])):                    
                remaining4cycle.append(remainings[i][j])            
        remainings_cycle.append(remaining4cycle)    
   
    if priority==1:
        selection.sort(key=lambda r: (-r[1],r[2],-r[3],r[4],r[5]))
    elif priority==2:
        selection.sort(key=lambda r: (-r[1],-r[3],r[2],r[4],r[5]))
    else:
        selection.sort(key=lambda r: (-r[1],r[4],r[2],-r[3],r[5]))
        
    idx_max=selection[0][0]    

    #print(selection)
    #print("idx_max:",idx_max)        
        
    placed_rectangles=placed_rectangles_cycle[idx_max]
    leftover_rects=leftover_cycle[idx_max]
    remaining_rects=remainings_cycle[idx_max]
    xtick = xtick_cycle[idx_max]
    ytick = ytick_cycle[idx_max]

    if cut_mode == 2: #转置回去        
        big_rect = Rectangle(big_rect.height,big_rect.width,big_rect.direction,big_rect.num,big_rect.id,big_rect.producer)           
        placed_rectangles = [{'rect':Rectangle(placed['rect'].height,placed['rect'].width,placed['rect'].direction,1,placed['rect'].id,placed['rect'].producer,placed['rect'].orderNo),'x':placed['y'],'y':placed['x'],'rotated':False} for placed in placed_rectangles]
        leftover_rects = [{'x':leftover['y'],'y':leftover['x'],'width':leftover['height'],'height':leftover['width']} for leftover in leftover_rects]            
        remaining_rects = [Rectangle(rect.height,rect.width,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo) for rect in remaining_rects]
        xtick = ytick_cycle[idx_max]
        ytick = xtick_cycle[idx_max]

    return selection[0], placed_rectangles, leftover_rects, remaining_rects, xtick, ytick


def merge_leftovers(leftover_rects, big_rect):
    # 余料数组内部合并
    merged_leftovers = []
    processed_indices = set()
    is_combine=0
   
    for i, leftover in enumerate(leftover_rects):
        if i in processed_indices or leftover['width'] <= 0 or leftover['height'] <= 0:
            continue
        is_combine=0
        # 检查是否在底部且宽度和高度都大于tresh
        if (leftover['y'] + leftover['height'] == big_rect.height and 
                leftover['width'] >= tresh and leftover['height'] >= tresh):
            for j, next_leftover in enumerate(leftover_rects):
                if(is_combine==1):
                    break
                if j in processed_indices or next_leftover['width'] <= 0 or next_leftover['height'] <= 0:
                    continue
                
                # 检查相邻的废料（高度大于该余料，且有一条边小于tresh）
                if (abs(next_leftover['x'] - (leftover['x'] + leftover['width'] + kerf)) <= kerf and
                        next_leftover['height'] > leftover['height'] and
                        (next_leftover['width'] < tresh or next_leftover['height'] < tresh)):
                    
                    # 合并余料的宽度，加上废料的宽度，减少废料的高度                    
                    leftover['width'] += next_leftover['width'] + kerf
                    if leftover['x']+leftover['width'] > big_rect.width:
                        leftover['width']-=kerf                        
                    next_leftover['height'] -= leftover['height']
                    is_combine=1
                    #next_leftover['y'] += leftover['height'] + kerf

                    if next_leftover['height'] <= 0:
                        processed_indices.add(j)

        merged_leftovers.append(leftover)
        processed_indices.add(i)
    
    # 合并相邻的余料
    final_merged_leftovers = []
    processed_indices = set()

    for i, leftover in enumerate(merged_leftovers):
        if i in processed_indices or leftover['width'] <= 0 or leftover['height'] <= 0:
            continue

        merged = leftover.copy()
        to_merge_indices = [i]
        
        for j in range(i + 1, len(merged_leftovers)):
            if(is_combine==1):
                break
            next_leftover = merged_leftovers[j]
            if (next_leftover['y'] == merged['y'] and next_leftover['height'] == merged['height'] and
                    next_leftover['width'] > 0 and next_leftover['height'] > 0 and
                    abs(next_leftover['x'] - (merged['x'] + merged['width'] + kerf)) <= kerf):
                
                merged['x'] = min(merged['x'], next_leftover['x'])
                merged['width'] = max(merged['x'] + merged['width'], next_leftover['x'] + next_leftover['width']) - merged['x']
                to_merge_indices.append(j)
         
        
        if len(to_merge_indices) > 1:
            final_merged_leftovers.append(merged)
            processed_indices.update(to_merge_indices)
        else:
            final_merged_leftovers.append(leftover)
                
    return final_merged_leftovers


def check_and_merge_small_pieces(placed_rectangles, final_leftovers):
    #合并小矩形与合适的余料
    small_leftovers = [leftover for leftover in final_leftovers if min(leftover['width'], leftover['height']) < tresh]
    
    for placed in placed_rectangles:
        for leftover in small_leftovers:
            if (placed['y'] == leftover['y'] and placed['rect'].height == leftover['height'] and
                abs(placed['x'] + placed['rect'].width + kerf - leftover['x']) <= kerf):
                # 合并水平方向上的矩形
                placed['rect'].width += leftover['width'] + kerf
                final_leftovers.remove(leftover)

            if (placed['x'] == leftover['x'] and placed['rect'].width == leftover['width'] and
                abs(placed['y'] + placed['rect'].height + kerf - leftover['y']) <= kerf):
                # 合并竖直方向上的矩形
                placed['rect'].height += leftover['height'] + kerf
                final_leftovers.remove(leftover)

# 计算统计信息
def calculate_statistics(big_rect, placed_rectangles, leftover_rects):
    total_area = big_rect.width * big_rect.height
    
    used_area = sum(placed['rect'].width * placed['rect'].height for placed in placed_rectangles)

    left_area=0
    left_num=0
    waste_area=0
    maxleft=0
    for rect in leftover_rects:        
        if rect['width'] > 0 and rect['height'] > 0: # 排除任何边为负的数据
            left_num += 1
            area = rect['width'] * rect['height']
            left_area += area
            if rect['width'] < tresh or rect['height'] < tresh:
                waste_area += area
            if maxleft < area:
                maxleft = area 
    
    loss_area = total_area - used_area - left_area     
    
    return used_area/total_area,waste_area/total_area,maxleft/total_area,left_num,loss_area/total_area


# 可视化切割结果
def visualize_packing_page(big_rect, placed_rectangles, leftover_rects, xtick, ytick, save_path=None):
    global cut_mode    
    
    # 可视化
    H=0
    fig, ax = plt.subplots(figsize=(20, 15))
    ax.clear()
    ax.set_xlim(0, big_rect.width)
    ax.set_ylim(0, big_rect.height)
    ax.set_aspect('equal')
    plt.subplots_adjust(left=0, right=1, top=0.95, bottom=0)
    if(min(big_rect.width,big_rect.height)<500): #更改大矩形规格字体的高度
        H=0.15
    else:
        H=0
    plt.suptitle(f"{sizethick} * {big_rect.height} * {big_rect.width}", fontsize=20, y=0.85+H)
    multiple=1
    for placed in placed_rectangles:
        rect = placed['rect']        
        x, y = placed['x'], placed['y']
        width, height = rect.width, rect.height
        rotation_text = "R" if placed['rotated'] else ""
        rect_patch = patches.Rectangle((x, y), width, height, edgecolor='blue', facecolor='cyan', alpha=0.5)
        ax.add_patch(rect_patch)
        
        if(min(big_rect.width,big_rect.height)<500):
         multiple=6  #改变字体倍数
        else:
            multiple=1

        font_size = min(rect.width, rect.height) * 0.06*multiple
        font_size = min(font_size, 10)  # 设置最大字体大小为10
        ax.text(x + width / 2, y + height / 2, f"{width}x{height}\n{rotation_text}",ha='center', va='center', fontsize=font_size, color='black')
        if show_orderNo:
            ax.text(x + width / 2, y + height / 4, f"{rect.orderNo[0]}",ha='center', va='center', fontsize=12, color='blue')

    # 绘制余料和废料
    for leftover in leftover_rects:
        if leftover['width'] > 0 and leftover['height'] > 0:            
            x, y = leftover['x'], leftover['y']
            width, height = leftover['width'], leftover['height']
            color = 'orange' if width >= tresh and height >= tresh else 'gray'
            leftover_patch = patches.Rectangle((x, y), width, height, edgecolor='black', facecolor=color, alpha=0.5)
            ax.add_patch(leftover_patch)
            label = "waste" if width < tresh or height < tresh else "left"
            if(min(big_rect.width,big_rect.height)<500):#改变字体倍数
              multiple=6
            else:
             multiple=1
            font_size = min(leftover['width'], leftover['height']) * 0.06*multiple
            font_size = min(font_size, 10)  # 设置最大字体大小为10
            ax.text(x + width / 2, y + height / 2, f"{label}\n{width}x{height}",
                    ha='center', va='center', fontsize=font_size, color='black')

    # 设置 x 轴和 y 轴的刻度
    ax.set_xticks(xtick)
    ax.set_yticks(ytick)

    # 让 xticks 显示在上侧
    ax.xaxis.set_ticks_position('top')

    plt.gca().invert_yaxis()
  
    # 保存jpg图片
    if save_path:
        plt.savefig(save_path, format='jpg', dpi=300, bbox_inches='tight')     
    
    plt.close(fig)
    return leftover_rects


def perform_back_calculation(max_width,max_height,min_width,min_height):
    global all_used_panel,all_placed_rectangles,total_cut_rects,all_leftover_rects,all_remaining_rects,all_statistics,all_xticks,all_yticks
    global remaining_rects,style,group_combine,cut_mode,priority,xstart_list,ystart_list,kerf,tresh

    while remaining_rects:
        #按最大尺寸作为初始尺寸
        big_rect = Rectangle(max_width,max_height,0,1,1) 
        all_remaining_rects.append(remaining_rects)

        # 四种排版方式循环 
        selection = []        
        placed_rectangles_cycle = []
        leftover_cycle = []        
        max_size_cycle = []        
        idx=0
        for cycle in range(4):

            if cycle==0:
                style=1
                group_combine=1
            elif cycle==1:
                style=2
                group_combine=1
            elif cycle==2:
                style=1
                group_combine=2
            elif cycle==3:
                style=2
                group_combine=2            
            
            #print("style:",style,"group_combine",group_combine)

            remaining4cycle=copy.deepcopy(remaining_rects)            
            
            remainings=[]
            unmatch_rects=[]
            if style==1:
                for rect in remaining4cycle:
                    if rect.producer != "" and rect.producer != big_rect.producer:  #不满足厂家匹配需求
                        unmatch_rects.append(rect)
                        continue 
                     
                    flag=0
                    for i in range(len(remainings)):  
                        if rect.width == remainings[i][0].width and rect.producer == remainings[i][0].producer:
                            remainings[i].append(Rectangle(rect.width, rect.height,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo))
                            flag=1
                    if flag==0:
                        remainings.append([Rectangle(rect.width, rect.height,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo)])
            else:
                for rect in remaining4cycle: 
                    if rect.producer != "" and rect.producer != big_rect.producer:  #不满足厂家匹配需求
                        unmatch_rects.append(rect)
                        continue  

                    flag=0
                    for i in range(len(remainings)):  
                        if rect.height == remainings[i][0].height and rect.producer == remainings[i][0].producer:
                            remainings[i].append(Rectangle(rect.width,rect.height,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo))
                            flag=1
                    if flag==0:                        
                        remainings.append([Rectangle(rect.width,rect.height,rect.direction,rect.num,rect.id,rect.producer,rect.orderNo)])
            
            #for i in range(len(remainings)):
            #    for j in range(len(remainings[i])):                    
            #        rect=remainings[i][j]
            #        print([i,j],[rect.width,rect.height,rect.direction,rect.num])
            #    print('\n')     
            
            placed_rectangles = []
            leftover_rects = []  # 当前大矩形的余料数组            
            x_start = [0]
            y_start = [0]
            xstart_list = [0]
            ystart_list = [0] 
            remainings = place_rectangles_vertically(x_start, y_start, big_rect, big_rect, remainings, placed_rectangles, 1, leftover_rects)
            if not remainings:
                # 没有剩余小矩形时，继续递归查找大矩形剩余部分
                place_rectangles_vertically(x_start, y_start, big_rect, big_rect, [], placed_rectangles, 1, leftover_rects)
                        
            utilization,waste_rate,maxleft,left_num,loss_rate=calculate_statistics(big_rect, placed_rectangles, leftover_rects)            
            #print("||utilization",utilization,"waste_rate",waste_rate,"maxleft:",maxleft,"left_num:",left_num,"loss_rate",loss_rate)            

            max_xstart = max(xstart_list)
            max_ystart = max(ystart_list)
            
            print('max_size:',[max_xstart,max_ystart])
            max_size_cycle.append([max_xstart,max_ystart]) 
            selection.append([idx,utilization,max_xstart])            
            placed_rectangles_cycle.append(placed_rectangles)
            leftover_cycle.append(leftover_rects)
            idx+=1    
        
        selection.sort(key=lambda r: (-r[1],r[2]))    #利用率从大到小，整板宽度从小到大

        print(selection)    

        #选择最优尺寸重新切割 
        idx = selection[0][0]  
        big_rect = Rectangle(max_size_cycle[idx][0],max_size_cycle[idx][1],0,1,1)  
        
        order_rects = copy.deepcopy(remaining_rects)
        
        statistics, placed_rectangles, leftover_rects, order_rects, xtick, ytick = pack_rectangles(big_rect, order_rects)

        # print("idx",idx)
        # print([big_rect.width,big_rect.height])
        # print(statistics)     
                
        while xtick[-1]<big_rect.width or ytick[-1]<big_rect.height: #重新切割后右侧有余料
            big_rect = Rectangle(xtick[-1],ytick[-1],0,1,1)
            order_rects = copy.deepcopy(remaining_rects)
            statistics, placed_rectangles, leftover_rects, order_rects, xtick, ytick = pack_rectangles(big_rect, order_rects)  
                            
        all_used_panel.append(big_rect)
        all_placed_rectangles.append(placed_rectangles)
        all_leftover_rects.append(leftover_rects)                
        all_statistics.append(statistics)
        all_xticks.append(xtick)
        all_yticks.append(ytick)
        total_cut_rects += len(placed_rectangles)    
            
        remaining_rects = copy.deepcopy(order_rects)    

def merge_used_panel():
    global used_rects, max_types

    #相同尺寸合并数量
    used_count = len(used_rects)
    # print("used_count:",used_count)
    rect_dict = {}
    for i in range(used_count):
        key = (used_rects[i].width, used_rects[i].height)
        if key in rect_dict:
            rect_dict[key] += 1
        else:
            rect_dict[key] = 1           
    
    num_types =  len(rect_dict) 
    num_types0 = num_types
    # print("num_types:",num_types)
    while max_types < num_types:
        # 合并尺寸规格    
        matrix = [[0 for _ in range(used_count)] for _ in range(used_count)]

        for i in range(used_count):
            for j in range(used_count):
                m = used_rects[i]
                n = used_rects[j]
                matrix[i][j] = n.width*n.height-m.width*m.height

        # 初始化最小值和其索引
        min_value = 1E20
        min_i, min_j = -1, -1
        
        # 遍历矩阵的每一行和每一列
        for i in range(used_count):
            for j in range(used_count):
                if used_rects[i].width == used_rects[j].width and used_rects[i].height == used_rects[j].height:
                    continue
                if used_rects[i].width > used_rects[j].width or used_rects[i].height > used_rects[j].height:
                    continue
                # 发现更小的元素时，更新最小值和索引
                if matrix[i][j] < min_value:
                    min_value = matrix[i][j]        

        for i in range(used_count):
            for j in range(used_count):
                if matrix[i][j] == min_value:  
                    used_rects[i]=used_rects[j]                    

        #相同尺寸合并数量
        used_count = len(used_rects)        
        rect_dict = {}
        for i in range(used_count):
            key = (used_rects[i].width, used_rects[i].height)
            if key in rect_dict:
                rect_dict[key] += 1
            else:
                rect_dict[key] = 1

        num_types = len(rect_dict)
        # print("num_types:",num_types)     
        if(num_types == num_types0):  #防止max_type太小而进入死循环
            break 
        num_types0 = num_types

    if max_types < num_types:
        msg = "警告：规格限制过于严格,最终排版规格数为："+str(num_types)
        print(msg)

    
    merged_panels = []   
    for key, quantity in rect_dict.items():       
        merged_panels.append([key[0], key[1], quantity])  

    big_rects = []   
    for i in range(used_count):       
        big_rects.append(used_rects[i]) 

    return merged_panels, big_rects
        

def merge_big_rects(big_rects):    
    #相同尺寸合并数量
    used_count = len(big_rects)
    rect_dict = {}
    for i in range(used_count):
        key = (big_rects[i].width, big_rects[i].height)
        if key in rect_dict:
            rect_dict[key] += 1
        else:
            rect_dict[key] = 1
            
    merged_panels = []   
    for key, quantity in rect_dict.items():       
        merged_panels.append([key[0], key[1], quantity])   

    return  merged_panels   

# 用料反算
def back_calculate_click(small_rects):       
    global cut_mode,style,group_combine,priority,xstart_list,ystart_list,kerf,tresh
    global all_used_panel, all_placed_rectangles, total_cut_rects, all_leftover_rects, all_remaining_rects,all_statistics, remaining_rects, all_xticks, all_yticks 
    global used_rects   
    global min_width, max_width, min_height, max_height, max_weight, material_density

    cut_mode = 1  
    
    remaining_rects = copy.deepcopy(small_rects)  # 剩余的矩形
    all_used_panel = []
    all_placed_rectangles = []  # 所有已放置的矩形
    total_cut_rects = 0  # 总切割数    
    all_leftover_rects = []  # 所有大矩形的余料数组
    all_remaining_rects = [] #当前对应的未排版数组
    all_statistics = []
    all_xticks = []
    all_yticks = []           

    remaining_rects.sort(key=lambda r: -r.width*r.height)  # Sort by first single area 
    for rect in remaining_rects:
        if rect.width >= min_width and rect.width <= max_width and rect.height >= min_height and rect.height <= max_height:
            for _ in range(rect.num):
                big_rect=Rectangle(rect.width,rect.height)
                all_used_panel.append(big_rect) 
                all_placed_rectangles.append({'rect': Rectangle(rect.width,rect.height, rect.direction, 1, rect.id, rect.producer, [rect.orderNo[0]]), 'x': 0, 'y': 0, 'rotated': False})
                all_statistics.append([0,big_rect.width*big_rect.height,0,0,0,0,1])
                all_xticks.append([0,big_rect.width])
                all_yticks.append([0,big_rect.height])
                total_cut_rects += 1
            remaining_rects.remove(rect) 

    # 寻找最大宽度和高度
    order_max_width = 0
    order_max_height = 0
    order_width = 0
    order_height = 0
    for rect in remaining_rects:        
        if rect.direction == 1:
            order_width = rect.width
            order_height = rect.height
        elif rect.direction == 2:
            order_width = rect.height
            order_height = rect.width
        else:
            order_width = max(rect.width,rect.height)
            order_height = min(rect.width,rect.height)
            
        if order_width > order_max_width:
            order_max_width = order_width
        if order_height > order_max_height:
            order_max_height = order_height

    print('order_max_width:',order_max_width,'order_max_height:',order_max_height)
    global msg
    if order_max_width > max_width:
        max_width = order_max_width
        msg = "警告：有订单长度超过设定范围,按最大订单长度排版！"
        print(msg)
    if order_max_height > max_height:
        max_height = order_max_height
        msg = "警告：有订单宽度超过设定范围,按最大订单宽度排版！"
        print(msg)

    #根据最大重量修订最大宽度
    width_limit = int(max_weight*1E9/max_height/sizethick/material_density+0.5)
    if width_limit < max_width:         
        max_width = width_limit          
        
    perform_back_calculation(max_width,max_height,min_width,min_height)    

    



    # 最后一张板不满足尺寸范围
    used_count = len(all_used_panel)
    print("used_count:",used_count)
    last_idx = used_count-1

    if all_used_panel[last_idx].width < min_width and len(all_xticks[last_idx-1]) >= 5 and len(all_remaining_rects) >= last_idx:
        remaining_rects = all_remaining_rects[last_idx-1] #倒数第二张
        width = int((all_used_panel[last_idx-1].width + all_used_panel[last_idx].width)/2) + tresh     

        total_cut_rects -= len(all_placed_rectangles[last_idx]) + len(all_placed_rectangles[last_idx-1])
        del all_used_panel[last_idx-1:used_count]   
        del all_placed_rectangles[last_idx-1:used_count]   
        del all_leftover_rects[last_idx-1:used_count]  
        del all_statistics[last_idx-1:used_count]
        del all_xticks[last_idx-1:used_count]
        del all_yticks[last_idx-1:used_count]  
        del all_remaining_rects[last_idx-1:used_count]   

        perform_back_calculation(width,max_height,min_width,min_height)

    # 合并用料
    used_rects = copy.deepcopy(all_used_panel)
    merged_panels, big_rects = merge_used_panel()
    cut_again(big_rects, small_rects)

    return merged_panels, big_rects

        
            
def get_xyticks(xstart_list,ystart_list):
    xtick=[]
    ytick=[]
    num=len(xstart_list)
    for i in range(num):
        if xstart_list[i]==0:
            ytick.append(ystart_list[i])
        if ystart_list[i]==0:
            xtick.append(xstart_list[i])
    ytick.append(max(ystart_list))

    sorted(set(xtick))
    sorted(set(ytick))  

    return xtick, ytick

 

def cut_again(big_rects, small_rects):      
    merged_panels = merge_big_rects(big_rects)         
    max_types = len(merged_panels)
    print("用料规格数：", max_types)
    print("用料信息：")
    for big_rect in big_rects:
        print([big_rect.width, big_rect.height])    
    
    performing_cut(big_rects,small_rects)
 

def performing_cut(big_rects,small_rects):
    global cut_mode,style,group_combine,priority,all_statistics,xstart_list,ystart_list,kerf,tresh,minratio
    global all_used_panel, all_placed_rectangles, total_cut_rects, all_leftover_rects, remaining_rects, all_xticks, all_yticks
    global total_order_count
    
    remaining_rects = copy.deepcopy(small_rects)  # 剩余的矩形
    all_used_panel = []
    all_placed_rectangles = []  # 所有已放置的矩形
    total_cut_rects = 0  # 总切割数    
    all_leftover_rects = []  # 所有大矩形的余料数组
    all_statistics = []
    all_xticks = []
    all_yticks = [] 

    for big_rect in big_rects:

        #print([big_rect.width,big_rect.height])    

        if remaining_rects:        
            statistics, placed_rectangles, leftover_rects, remaining_rects, xtick, ytick  = pack_rectangles(big_rect, remaining_rects)    

            # if statistics[1]/(big_rect.width*big_rect.height) < minratio:              
            #     messagebox.showwarning("警告", f"有整板利用率低于设定值，\n请修改参数后重新分割！")  

            all_used_panel.append(big_rect)
            all_placed_rectangles.append(placed_rectangles)
            all_leftover_rects.append(leftover_rects)                
            all_statistics.append(statistics)
            all_xticks.append(xtick)
            all_yticks.append(ytick)
            total_cut_rects += len(placed_rectangles)      
    global msg
    if total_cut_rects == total_order_count:
        msg = "正常：运行结束"
        print(msg)
    else:
        msg = "警告：有订单未排版!请放宽规格限制后重试"
        print(msg)



def main():
    parser = argparse.ArgumentParser(description="Rectangle Packing")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--data', type=str, help='Input data in custom format')
    input_group.add_argument('--input-file', type=str, help='Read JSON input from a UTF-8 file')

    args = parser.parse_args()

    try:
        if args.input_file:
            with open(args.input_file, 'r', encoding='utf-8') as input_file:
                data = json.load(input_file)
        else:
            jsonstr = args.data.replace("%", "\"")
            data = json.loads(jsonstr)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error parsing JSON: {e}")
        return
   
    global kerf, tresh, cut_mode, priority, left_merge, sizethick, material_density, show_orderNo
    global min_width, max_width, min_height, max_height, max_weight, minratio, max_types
    global total_order_count,msg

    max_width = data.get("max_long", 4000)    #最大长度限制
    min_width = data.get("min_long", 3000)    #最小长度限制
    max_height = data.get("max_wide", 1500)    #最大宽度限制
    min_height = data.get("min_wide", 1000)    #最小宽度限制
    max_weight = data.get("max_weight", 7.84)    #最大重量限制   
    minratio = data.get("min_rate", 0.85)    #最小利用率 
    kerf = data.get("kerf", 5)    # 设置刀口厚度
    tresh = data.get("tresh", 50)  # 设置废料尺寸
    sizethick = data.get("thickness", 20)  # 材料厚度
    material_density = data.get("density", 2.8)  # 材料密度
    max_types = data.get("max_specs", 20)    #最多规格限制 
    cut_mode = data.get("cut_mode", 1)  # 设置切割模式 1-竖切 2-横切
    priority = data.get("priority", 1)   # 设置排序优先类型 1-废料最小优先 2-余料最大优先 3-余料最少优先
    left_merge=data.get("left_merge",1)  #废料是否吞并 1-废料保留 2-合并余料后吞并废料 3-吞并废料后合并余料    
    show_orderNo = data.get("printNo",False)   

    order_rects = []
    total_order_count = 0
    for order in data["orderForm"]:
        if "producer" in order: 
            producer = order["producer"]
        else:
            producer = ""   
        if "orderNo" in order:
            orderNo = [order["orderNo"]] * order["num"]                
        else:
            orderNo = [1] * order["num"]             
        order_rects.append(Rectangle(int(order["sizelong"]), int(order["sizewide"]), order["direction"], order["num"], order["id"], producer, orderNo))     
        total_order_count += order["num"]
    print("订单需求量：",total_order_count)

    small_rects = []
    small_rects.append(order_rects[0]) 
    for order in order_rects[1:]:
        flag=0
        for idx in range(len(small_rects)):            
            if order.width == small_rects[idx].width and order.height == small_rects[idx].height and order.direction == small_rects[idx].direction and order.producer == small_rects[idx].producer:   #合并订单              
                small_rects[idx].num += order.num
                small_rects[idx].orderNo = small_rects[idx].orderNo + order.orderNo
                flag=1
                break
        if flag==0:
            small_rects.append(order)   
    
    # for rect in small_rects:
    #     print("small_rect producer:",rect.producer," num:",rect.num, "No.", rect.orderNo) 

    big_rects = []
    if "materials" in data:
        for mat in data["materials"]:
            if "producer" in mat: 
                big_rects.append(Rectangle(mat["sizelong"], mat["sizewide"],0, mat["num"], mat["id"], mat["producer"]))
            else:
                big_rects.append(Rectangle(mat["sizelong"], mat["sizewide"],0, mat["num"], mat["id"], ""))
        big_rects.sort(key=lambda r: r.width*r.height)  # Sort by area
    

    if not big_rects: #material为空
        print('开始反算') 
        merged_panels, big_rects = back_calculate_click(small_rects)
    else:        
        print('重新切割')       
        cut_again(big_rects, small_rects)     

    
    used_count = len(all_used_panel)
    if used_count > 0:     

        output_data = {
            "cutId": data["cutId"],
            'msg': msg,
            "forceParam": data.get("forceParam","0"),
            "otherParam": data.get("otherParam"),
            "unfinished": [rect.id for rect in remaining_rects],
            "result": []
        }
        
        for i in range(len(all_used_panel)):

            big_rect = all_used_panel[i]
            placed_rectangles = all_placed_rectangles[i]

            utilization = all_statistics[i][1]
            waste_rate = all_statistics[i][2]
            maxleft = all_statistics[i][3]
            left_num = all_statistics[i][4]        
            loss_rate = all_statistics[i][5]
            finished_ids = [placed["rect"].id for placed in placed_rectangles]

            random_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])
            img_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{i+1}_{random_id}.jpg"

            current_time = datetime.now().strftime("%Y-%m-%d")
            folder_name = f"{current_time}"
            image_root = os.environ.get("BACKCAL_IMAGE_ROOT", r"D:\images")
            img_file_folder_path = os.path.join(image_root, folder_name)
            if not os.path.exists(img_file_folder_path):
                os.makedirs(img_file_folder_path)
            img_file_path = rf'{img_file_folder_path}\{img_name}'

            final_leftovers = visualize_packing_page(big_rect, placed_rectangles, all_leftover_rects[i], all_xticks[i], all_yticks[i], save_path=img_file_path)

            data = [
                {
                    "sizelong": leftover["width"],
                    "sizewide": leftover["height"]
                }
                for leftover in final_leftovers if leftover["width"] >= tresh and leftover["height"] >= tresh
            ]

            output_data["result"].append({
                "id": big_rect.id,
                "producer":big_rect.producer,
                'sizelong':big_rect.width,
                'sizewide':big_rect.height,
                "cut_rate": round(utilization,4),
                "left_num": left_num,
                "waste_rate": round(waste_rate,4),
                "leftover_rate": max(0, 1-round(utilization,4)-round(waste_rate,4)-round(loss_rate,4)),
                "max_left": maxleft,            
                "loss_rate": round(loss_rate,4),
                "finish": finished_ids,
                "img": rf'{folder_name}/{img_name}',
                "data": data                
            })
        # if output_data:  # 确保有结果才发送和保存
        #     requests.post('http://localhost:7028/back/cal/receive', json=output_data)

        result_file = os.environ.get("BACKCAL_RESULT_FILE", 'cut_results.json')
        result_parent = os.path.dirname(os.path.abspath(result_file))
        os.makedirs(result_parent, exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
    else:
        output_data = {
            "cutId": data["cutId"],
            "forceParam": data.get("forceParam","0"),
            "otherParam": data.get("otherParam"),
            "unfinished": [rect.id for rect in remaining_rects],
            "result": []
        }
        result_file = os.environ.get("BACKCAL_RESULT_FILE", 'cut_results.json')
        result_parent = os.path.dirname(os.path.abspath(result_file))
        os.makedirs(result_parent, exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)

    print("Processing complete. Output saved to 'cut_results.json'.")

if __name__ == "__main__":
    main()
