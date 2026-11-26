你好，我是王争。初六好！

为了帮你巩固所学，真正掌握数据结构和算法，我整理了数据结构和算法中，必知必会的30个代码实现，分7天发布出来，供你复习巩固所用。今天是第六篇。

和之前一样，你可以花一点时间，来手写这些必知必会的代码。写完之后，你可以根据结果，回到相应章节，有针对性地进行复习。做到这些，相信你会有不一样的收获。

* * *

## 关于图的几个必知必会的代码实现

### 图

- 实现有向图、无向图、有权图、无权图的邻接矩阵和邻接表表示方法
- 实现图的深度优先搜索、广度优先搜索
- 实现Dijkstra算法、A\*算法
- 实现拓扑排序的Kahn算法、DFS算法

## 对应的LeetCode练习题（@Smallfly 整理）

- Number of Islands（岛屿的个数）

英文版：[https://leetcode.com/problems/number-of-islands/description/](https://leetcode.com/problems/number-of-islands/description/)

中文版：[https://leetcode-cn.com/problems/number-of-islands/description/](https://leetcode-cn.com/problems/number-of-islands/description/)

- Valid Sudoku（有效的数独）

英文版：[https://leetcode.com/problems/valid-sudoku/](https://leetcode.com/problems/valid-sudoku/)

中文版：[https://leetcode-cn.com/problems/valid-sudoku/](https://leetcode-cn.com/problems/valid-sudoku/)

* * *

做完题目之后，你可以点击“请朋友读”，把测试题分享给你的朋友，说不定就帮他解决了一个难题。

祝你取得好成绩！明天见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>色即是空</span> 👍（2） 💬（1）<p>有效数独，就是穷举遍历方法求解，跟这一节练习的图，没有什么关系啊！放这个题目的时候是怎么考虑的啊？</p>2019-06-27</li><br/><li><span>ext4</span> 👍（1） 💬（1）<p>有效的数独
class Solution {
  public:
    bool isValidSudoku(vector&lt; vector&lt;char&gt; &gt;&amp; board) {
      set&lt;char&gt; numset;
      for (int i = 0; i &lt; 9; i++) {
        numset.clear();
        for (int j = 0; j &lt; 9; j++) {
          char val = board[i][j];
          if (val != &#39;.&#39;) {
            if (numset.count(val) != 0) return false;
            numset.insert(val);
          }
        }
      }
      for (int j = 0; j &lt; 9; j++) {
        numset.clear();
        for (int i = 0; i &lt; 9; i++) {
          char val = board[i][j];
          if (val != &#39;.&#39;) {
            if (numset.count(val) != 0) return false;
            numset.insert(val);
          }
        }
      }
      for (int i = 0; i &lt; 3; i++) {
        for (int j = 0; j &lt; 3; j++) {
          numset.clear();
          for (int p = 0; p &lt; 3; p++) {
            for (int q = 0; q &lt; 3; q++) {
              char val = board[i * 3 + p][j * 3 + q];
              if (val != &#39;.&#39;) {
                if (numset.count(val) != 0) return false;
                numset.insert(val);
              }
            }
          }
        }
      }
      return true;
    }
};</p>2019-02-10</li><br/><li><span>Nereus</span> 👍（0） 💬（1）<p>
并查集—go实现
func numIslands(grid [][]byte) int {
	if len(grid) == 0 {
		return 0
	}

	N := len(grid)*len(grid[0]) + 1

	u := NewUnionSet(N)

	for i := 0; i &lt; len(grid); i ++ {
		for j := 0; j &lt; len(grid[i]); j ++ {
			if grid[i][j] == &#39;1&#39; {
				&#47;&#47; 联通下边
				if i+1 &lt; len(grid) {
					if grid[i+1][j] == &#39;1&#39; {
						u.join(i*len(grid[i])+j, (i+1)*len(grid[i])+j)
					}
				}

				&#47;&#47; 联通右边
				if j+1 &lt; len(grid[i]) {
					if grid[i][j+1] == &#39;1&#39; {
						u.join(i*len(grid[i])+j, i*len(grid[i])+j+1)
					}
				}
			} else {
				u.join(i*len(grid[i])+j, N-1)
			}
		}
	}

	return  u.counts() -1
}

type UnionSet []int

func NewUnionSet(n int) UnionSet {
	var u UnionSet
	u = make([]int, n)
	for i := 0; i &lt; len(u); i ++ {
		u[i] = i
	}
	return u

}

func (u UnionSet) find(i int) int {
	tmp := i
	for u[tmp] != tmp {
		tmp = u[tmp]
	}

	j := i
	for j != tmp {
		tt := u[j]
		u[j] = tmp
		j = tt
	}

	return tmp
}

func (u UnionSet) connected(i, j int) bool {
	return u.find(i) == u.find(j)
}

func (u UnionSet) counts() int {
	var count int
	for idx, rec := range u {
		if idx == rec {
			count++
		}
	}
	return count
}

func (u UnionSet) join(i, j int) {
	x, y := u.find(i), u.find(j)
	if x != y {
		if y &gt; x {
			u[x] = y
		} else {
			u[y] = x
		}
	}
}
</p>2019-02-14</li><br/><li><span>拉欧</span> 👍（0） 💬（1）<p>Number of Islands（岛屿的个数）go语言实现，亲测通过：
func numIslands(grid [][]byte) int {

	isSearch:=make([][]int,len(grid))
	island:=0
	for i:=0;i&lt;len(isSearch);i++{
		isSearch[i]=make([]int,len(grid[0]))
	}
	for i,line:=range grid{
		for j,_:=range line{
			if isSearch[i][j]==0 &amp;&amp; grid[i][j]==&#39;1&#39;{
				Search(grid,isSearch,i,j)
				island++
			}

		}
	}
	return island
}

func Search(grid [][]byte,isSearch [][]int, i int,j int){
	if isSearch[i][j]==1{
		return
	}
	isSearch[i][j]=1
	if grid[i][j]==&#39;1&#39;{
		if i&gt;=1{
			Search(grid,isSearch,i-1,j)
		}
		if i&lt;len(grid)-1{
			Search(grid,isSearch,i+1,j)
		}
		if j&gt;=1{
			Search(grid,isSearch,i,j-1)
		}
		if j&lt;len(grid[0])-1{
			Search(grid,isSearch,i,j+1)
		}
	}else{
		return
	}
}
</p>2019-02-14</li><br/><li><span>蚂蚁内推+v</span> 👍（0） 💬（1）<p>    岛屿数Java实现
public int numIslands(char[][] grid) {
        int m = grid.length;
        if (m == 0) return 0;
        int n = grid[0].length;
        
        int ans = 0;
        for (int y = 0; y &lt; m; ++y)
            for (int x = 0; x &lt; n; ++x)
                if (grid[y][x] == &#39;1&#39;) {
                    ++ans;
                    dfs(grid, x, y, n, m);
                }
        
        return ans;
    }
    
    private void dfs(char[][] grid, int x, int y, int n, int m) {
        if (x &lt; 0 || y &lt; 0 || x &gt;= n || y &gt;= m || grid[y][x] == &#39;0&#39;)
            return;
        grid[y][x] = &#39;0&#39;;
        dfs(grid, x + 1, y, n, m);
        dfs(grid, x - 1, y, n, m);
        dfs(grid, x, y + 1, n, m);
        dfs(grid, x, y - 1, n, m);
    }</p>2019-02-11</li><br/><li><span>mgxian</span> 👍（0） 💬（1）<p>有效的数独 go 语言实现
package main

import (
	&quot;fmt&quot;
)

func hasRepeatedNumbers(numbers []byte) bool {
	var numbersExistFlag [9]bool
	for _, num := range numbers {
		if num == &#39;.&#39; {
			continue
		}
		index := num - &#39;0&#39; - 1
		if numbersExistFlag[index] {
			return true
		}
		numbersExistFlag[index] = true
	}
	return false
}

func isValidSudoku(board [][]byte) bool {
	sudokuSize := 9
	sudokuUnitSize := 3
	for _, line := range board {
		if hasRepeatedNumbers(line) {
			return false
		}
	}

	for columnIndex := 0; columnIndex &lt; sudokuSize; columnIndex++ {
		columnNumbers := make([]byte, 0)
		for lineIndex := 0; lineIndex &lt; sudokuSize; lineIndex++ {
			columnNumbers = append(columnNumbers, board[lineIndex][columnIndex])
		}
		if hasRepeatedNumbers(columnNumbers) {
			return false
		}
	}

	sudokuUnitCountEachLine := sudokuSize &#47; sudokuUnitSize
	for i := 0; i &lt; sudokuUnitCountEachLine; i++ {
		for j := 0; j &lt; sudokuUnitCountEachLine; j++ {
			sudokuUnitNumbers := make([]byte, 0)
			for _, line := range board[i*3 : (i+1)*3] {
				sudokuUnitNumbers = append(sudokuUnitNumbers, line[j*3:(j+1)*3]...)
			}

			if hasRepeatedNumbers(sudokuUnitNumbers) {
				return false
			}
		}
	}

	return true
}

func main() {
	testData1 := [][]byte{
		{&#39;5&#39;, &#39;3&#39;, &#39;.&#39;, &#39;.&#39;, &#39;7&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;},
		{&#39;6&#39;, &#39;.&#39;, &#39;.&#39;, &#39;1&#39;, &#39;9&#39;, &#39;5&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;},
		{&#39;.&#39;, &#39;9&#39;, &#39;8&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;6&#39;, &#39;.&#39;},
		{&#39;8&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;6&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;3&#39;},
		{&#39;4&#39;, &#39;.&#39;, &#39;.&#39;, &#39;8&#39;, &#39;.&#39;, &#39;3&#39;, &#39;.&#39;, &#39;.&#39;, &#39;1&#39;},
		{&#39;7&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;2&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;6&#39;},
		{&#39;.&#39;, &#39;6&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;2&#39;, &#39;8&#39;, &#39;.&#39;},
		{&#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;4&#39;, &#39;1&#39;, &#39;9&#39;, &#39;.&#39;, &#39;.&#39;, &#39;5&#39;},
		{&#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;.&#39;, &#39;8&#39;, &#39;.&#39;, &#39;.&#39;, &#39;7&#39;, &#39;9&#39;}}
	fmt.Println(isValidSudoku(testData1))
}</p>2019-02-10</li><br/><li><span>kai</span> 👍（3） 💬（0）<p>今天根据老师的课程，总结了一下图的相关知识点，然后用代码实现了一下图的相关的算法，感觉图还是要难于其他数据结构，需要接着多练习~</p>2019-02-10</li><br/><li><span>李皮皮皮皮皮</span> 👍（3） 💬（0）<p>图很复杂😢</p>2019-02-10</li><br/><li><span>kai</span> 👍（1） 💬（0）<p>实现图的深度优先搜索、广度优先搜索:

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.Queue;

public class BFSAndDFS {

    class Node {
        public int value; &#47;&#47;Node 值
        public int in;    &#47;&#47;入度：指向该节点的边有几条
		public int out;   &#47;&#47;出度：指向其他节点的边有几条
		public ArrayList&lt;Node&gt; nexts;
		public ArrayList&lt;Edge&gt; edges;

		public Node(int value) {
			this.value = value;
			this.in = 0;
			this.out = 0;
			this.nexts = new ArrayList&lt;&gt;();
			this.edges = new ArrayList&lt;&gt;();
		}
	}
	
    public static void bfs(Node node) {
        if (node == null) {
            return;
        }

        Queue&lt;Node&gt; queue = new LinkedList&lt;&gt;();
        HashSet&lt;Node&gt; set = new HashSet&lt;&gt;();
        queue.add(node);
        set.add(node);
        while (!queue.isEmpty()) {
            Node cur = queue.poll();
            System.out.print(cur.value + &quot; &quot;);
            for (Node next : cur.nexts) {
                if (!set.contains(next)) {
                    queue.add(next);
                    set.add(next);
                }
            }
        }
    }

    public static void dfs(Node node) {
        if (node == null) {
            return;
        }

        Stack&lt;Node&gt; stack = new Stack&lt;&gt;();
        HashSet&lt;Node&gt; set = new HashSet&lt;&gt;();
        stack.push(node);
        set.add(node);
        System.out.print(node.value + &quot; &quot;);
        while (!stack.isEmpty()) {
            Node cur = stack.pop();
            for (Node next : cur.nexts) {
                if (!set.contains(next)) { 
                    stack.push(cur);       
                    stack.push(next);
                    set.add(next);         
                    System.out.print(next.value + &quot; &quot;);
                    break;                
                }
            }
        }
    }
}</p>2019-02-11</li><br/><li><span>纯洁的憎恶</span> 👍（1） 💬（1）<p>1.在邻接矩阵中找出连通图个数即可。在每个顶点执行DFS或BFS，执行次数即为岛屿数，也可以使用并查集。

2. 依次考察9✖️9数独各行各列是否有重复数字（可以用9位数组统计），然后再考察每个3✖️3子矩阵是否有重复数字。都没有则成功。</p>2019-02-10</li><br/><li><span>杨建斌(young)</span> 👍（0） 💬（0）<p>有效数独
int[][] row = new int[10][10];
        int[][] col = new int[10][10];

        boolean retFlag = true;
        for (int i = 0; i &lt; grid.length; i += 3) {
            for (int j = 0; j &lt; grid[0].length; j += 3) {
                boolean xx = xx(row, col, grid, i, j);&#47;&#47;模块左上角第一个元素位置
                if (!xx) {
                    retFlag = false;
                    break;
                }
            }
            if (!retFlag) {
                break;
            }
        }
public static boolean xx(int[][] row, int[][] col, String[][] grid, int i, int j) {
        Map map = new HashMap();
        for (int ii = i; ii &lt; i + 3; ii++) {
            for (int jj = j; jj &lt; j + 3; jj++) {
                if (map.get(grid[ii][jj]) != null) {
                    return false;
                }
                if (!&quot;.&quot;.equals(grid[ii][jj])) {
                    map.put(grid[ii][jj], &quot;1&quot;);
                    int haveRow = row[ii][Integer.parseInt(grid[ii][jj])];
                    int haveCol = col[jj][Integer.parseInt(grid[ii][jj])];
                    if (haveCol == 1 || haveRow == 1) {
                        return false;
                    }
                    row[ii][Integer.parseInt(grid[ii][jj])] = col[jj][Integer.parseInt(grid[ii][jj])] = 1;
                }
            }
        }
        return true;
    }</p>2023-07-03</li><br/><li><span>杨建斌(young)</span> 👍（0） 💬（0）<p>岛屿的个数
public static void main(String[] args) {
        int[][] grid = new int[][]{
                {1, 1, 0, 0, 0},
                {1, 1, 0, 0, 0},
                {0, 0, 1, 0, 0},
                {0, 0, 0, 1, 1}
        };
        int cnt = 0;
        for (int i = 0; i &lt; grid.length; i++) {
            for (int j = 0; j &lt; grid[0].length; j++) {
                if (grid[i][j] == 1) {
                    xx(grid, i, j);
                    cnt++;
                }
            }
        }

        System.out.println(cnt);
    }

    public static void xx(int[][] grid, int i, int j) {
        if (i &lt; 0 || j &lt; 0 || i &gt;= grid.length || j &gt;= grid[0].length) {
            return;
        }
        if (grid[i][j] == 0) {
            return;
        }
        &#47;&#47;等于1
        grid[i][j] = 0;
        if (i &gt; 0) {
            xx(grid, i - 1, j);
        }
        if (j &gt; 0) {
            xx(grid, i, j - 1);
        }
        if (i &lt; grid.length - 1) {
            xx(grid, i + 1, j);
        }
        if (j &lt; grid[0].length - 1) {
            xx(grid, i, j + 1);
        }
    }</p>2023-07-03</li><br/><li><span>Geek_97afb1</span> 👍（0） 💬（0）<p>入坑第一百天
                       -brandon</p>2022-06-22</li><br/><li><span>Bax</span> 👍（0） 💬（0）<p>数独，还没测试</p>2022-02-18</li><br/><li><span>阿甘</span> 👍（0） 💬（0）<p>class Solution {
  public int numIslands(char[][] grid) {
        int num = 0;
        for (int i = 0; i &lt; grid.length; i++) { &#47;&#47; rows
            for (int j = 0; j &lt; grid[i].length; j++) { &#47;&#47; cols
                if (grid[i][j] == &#39;1&#39;) {
                    num++;
                    dfs(grid, i, j, grid.length, grid[i].length);
                }
            }
        }
        return num;
    }

    private void dfs(char[][] grid, int i, int j, int rows, int cols) {
        if (i &lt; 0 || j &lt; 0 || i &gt;= rows || j &gt;= cols || grid[i][j] == &#39;0&#39;) {
            return;
        }
        grid[i][j] = &#39;0&#39;; &#47;&#47; visit

        dfs(grid, i - 1, j, rows, cols);
        dfs(grid, i, j - 1, rows, cols);
        dfs(grid, i + 1, j, rows, cols);
        dfs(grid, i, j + 1, rows, cols);
    }
}</p>2021-06-29</li><br/>
</ul>