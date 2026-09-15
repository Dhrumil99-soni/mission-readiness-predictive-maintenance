# Data Structures — Fundamentals

## Arrays
- Fixed-size collection of elements of the same type
- Indexed from 0
- O(1) access, O(n) search, O(n) insert/delete (middle)

**Example:** int[] arr = {10, 20, 30, 40}

## Linked Lists
- Collection of nodes, each holding data + pointer to next node
- O(n) access, O(1) insert/delete at head
- Types: Singly, Doubly, Circular

**Use case:** Efficient insertions/deletions when index access is not needed.

## Stacks
- LIFO — Last In, First Out
- Operations: push, pop, peek
- O(1) push/pop
- Use case: function call stack, undo operations, bracket matching

## Queues
- FIFO — First In, First Out
- Operations: enqueue, dequeue
- O(1) enqueue/dequeue
- Use case: task scheduling, BFS traversal

## Trees
- Hierarchical structure with a root, branches, and leaves
- **Binary Tree:** each node has at most 2 children
- **Binary Search Tree (BST):** left < root < right
- Height-balanced BST (AVL): O(log n) search, insert, delete

## Hash Tables (Hash Maps)
- Key-value pairs with O(1) average lookup
- Hash function maps keys to indices
- Collisions handled by chaining or open addressing

**Example:** dictionary["apple"] = 5

## Big-O Complexity Summary
| Structure     | Access | Search | Insert | Delete |
|---------------|--------|--------|--------|--------|
| Array         | O(1)   | O(n)   | O(n)   | O(n)   |
| Linked List   | O(n)   | O(n)   | O(1)   | O(1)   |
| BST (balanced)| O(log n)| O(log n)| O(log n)| O(log n)|
| Hash Table    | N/A    | O(1)   | O(1)   | O(1)   |
