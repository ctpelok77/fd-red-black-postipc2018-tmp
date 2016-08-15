#include "merge_tree.h"

#include "../utils/rng.h"
#include "../utils/system.h"

#include <cassert>
#include <iostream>

using namespace std;

namespace merge_and_shrink {
const int UNINITIALIZED = -1;

MergeTreeNode::MergeTreeNode(int ts_index)
    : parent(nullptr),
      left_child(nullptr),
      right_child(nullptr),
      ts_index(ts_index) {
}

MergeTreeNode::MergeTreeNode(
    MergeTreeNode *left_child,
    MergeTreeNode *right_child)
    : parent(nullptr),
      left_child(left_child),
      right_child(right_child),
      ts_index(UNINITIALIZED) {
    left_child->parent = this;
    right_child->parent = this;
}

MergeTreeNode::~MergeTreeNode() {
    delete left_child;
    delete right_child;
    left_child = nullptr;
    right_child = nullptr;
}

MergeTreeNode *MergeTreeNode::get_left_most_sibling() {
    if (has_two_leaf_children()) {
        return this;
    }
    assert(left_child && right_child);

    if (!left_child->is_leaf()) {
        return left_child->get_left_most_sibling();
    }

    assert(!right_child->is_leaf());
    return right_child->get_left_most_sibling();
}

pair<int, int> MergeTreeNode::erase_children_and_set_index(int new_index) {
    assert(has_two_leaf_children());
    int left_child_index = left_child->ts_index;
    int right_child_index = right_child->ts_index;
    assert(left_child_index != UNINITIALIZED);
    assert(right_child_index != UNINITIALIZED);
    delete left_child;
    delete right_child;
    left_child = nullptr;
    right_child = nullptr;
    assert(ts_index == UNINITIALIZED);
    ts_index = new_index;
    return make_pair(left_child_index, right_child_index);
}

void MergeTreeNode::get_parents_of_ts_indices(
    const pair<int, int> &ts_indices,
    pair<MergeTreeNode *, MergeTreeNode *> &result) {
    if (result.first && result.second) {
        return;
    }

    MergeTreeNode *parent1 = nullptr;
    if (left_child && left_child->is_leaf() &&
        (left_child->ts_index == ts_indices.first ||
         left_child->ts_index == ts_indices.second)) {
        parent1 = this;
    }

    if (parent1) {
        if (result.first) {
            assert(!result.second);
            result.second = parent1;
        } else {
            result.first = parent1;
        }
    }

    MergeTreeNode *parent2 = nullptr;
    if (right_child && right_child->is_leaf() &&
        (right_child->ts_index == ts_indices.first ||
         right_child->ts_index == ts_indices.second)) {
        parent2 = this;
    }

    if (parent2) {
        if (result.first) {
            assert(!result.second);
            result.second = parent2;
        } else {
            result.first = parent2;
        }
    }

    if (left_child) {
        left_child->get_parents_of_ts_indices(ts_indices, result);
    }

    if (right_child) {
        right_child->get_parents_of_ts_indices(ts_indices, result);
    }
}

int MergeTreeNode::compute_num_internal_nodes() const {
    if (is_leaf()) {
        return 0;
    } else {
        int number_of_internal_nodes = 1; // count the node itself
        if (left_child) {
            number_of_internal_nodes += left_child->compute_num_internal_nodes();
        }
        if (right_child) {
            number_of_internal_nodes += right_child->compute_num_internal_nodes();
        }
        return number_of_internal_nodes;
    }
}

void MergeTreeNode::inorder(int offset, int current_indentation) const {
    if (right_child) {
        right_child->inorder(offset, current_indentation + offset);
    }
    for (int i = 0; i < current_indentation; ++i) {
        cout << " ";
    }
    cout << ts_index << endl;
    if (left_child) {
        left_child->inorder(offset, current_indentation + offset);
    }
}

MergeTree::MergeTree(
    MergeTreeNode *root,
    shared_ptr<utils::RandomNumberGenerator> rng,
    UpdateOption update_option)
    : root(root), rng(rng), update_option(update_option) {
}

MergeTree::~MergeTree() {
    delete root;
    root = nullptr;
}

pair<int, int> MergeTree::get_next_merge(int new_index) {
    MergeTreeNode *next_merge = root->get_left_most_sibling();
    return next_merge->erase_children_and_set_index(new_index);
}

pair<MergeTreeNode *, MergeTreeNode *> MergeTree::get_parents_of_ts_indices(
    const pair<int, int> &ts_indices) {
    pair<MergeTreeNode *, MergeTreeNode*> result = make_pair(nullptr, nullptr);
    root->get_parents_of_ts_indices(ts_indices, result);
    assert(result.first && result.second);
    return result;
}

void MergeTree::update(pair<int, int> merge, int new_index) {
    int ts_index1 = merge.first;
    int ts_index2 = merge.second;
    assert(root->ts_index != ts_index1 && root->ts_index != ts_index2);
    pair<MergeTreeNode *, MergeTreeNode *> parents = get_parents_of_ts_indices(merge);
    MergeTreeNode *first_parent = parents.first;
    MergeTreeNode *second_parent = parents.second;

    if (first_parent == second_parent) { // given merge already in the tree
        first_parent->erase_children_and_set_index(new_index);
    } else {
//        inorder_traversal(4);
//        cout << "updating: merge = " << merge << ", new index = " << new_index << endl;
        MergeTreeNode *surviving_node = nullptr;
        MergeTreeNode *removed_node = nullptr;
        if (update_option == UpdateOption::USE_FIRST) {
            surviving_node = first_parent;
            removed_node = second_parent;
        } else if (update_option == UpdateOption::USE_SECOND) {
            surviving_node = second_parent;
            removed_node = first_parent;
        } else if (update_option == UpdateOption::USE_RANDOM) {
            int random = (*rng)(2);
            surviving_node = (random == 0 ? first_parent : second_parent);
            removed_node = (random == 0 ? second_parent : first_parent);
        } else {
            ABORT("Unknown merge tree update option");
        }

        // Update the leaf node corresponding to one of the indices to
        // correspond to the merged index.
        MergeTreeNode *surviving_leaf = nullptr;
        if (surviving_node->left_child->ts_index == ts_index1 ||
            surviving_node->left_child->ts_index == ts_index2) {
            surviving_leaf = surviving_node->left_child;
        } else {
            assert(surviving_node->right_child->ts_index == ts_index1 ||
                surviving_node->right_child->ts_index == ts_index2);
            surviving_leaf = surviving_node->right_child;
        }
        surviving_leaf->ts_index = new_index;

        // Remove all links to removed_node and store pointers to the
        // relevant children and its parent.
        MergeTreeNode *parent_of_removed_node = removed_node->parent;
        if (parent_of_removed_node) {
            // parent_of_removed_node can be nullptr if removed_node
            // is the root node
            if (parent_of_removed_node->left_child == removed_node) {
                parent_of_removed_node->left_child = nullptr;
            } else {
                assert(parent_of_removed_node->right_child == removed_node);
                parent_of_removed_node->right_child = nullptr;
            }
        }
        MergeTreeNode *surviving_child_of_removed_node = nullptr;
        /*
          Find the child of remove_node that should survive (i.e. the node that
          does not correspond to the merged indices) and set it to null so that
          deleting removed_node later does not delete (via destructor) the
          surviving child.
        */
        if (removed_node->left_child->ts_index == ts_index1 ||
            removed_node->left_child->ts_index == ts_index2) {
            surviving_child_of_removed_node = removed_node->right_child;

            removed_node->right_child = nullptr;
        } else {
            assert(removed_node->right_child->ts_index == ts_index1 ||
                   removed_node->right_child->ts_index == ts_index2);
            surviving_child_of_removed_node = removed_node->left_child;
            removed_node->left_child = nullptr;
        }

        if (removed_node == root) {
            root = surviving_child_of_removed_node;
        }

        // Finally delete removed_node (this also deletes its child
        //corresponding to one of the merged indices, but not the other one).
        delete removed_node;
        removed_node = nullptr;

        // Update pointers of the surviving child of removed_node and the
        // parent of removed_node (if existing) to point to each other.
        surviving_child_of_removed_node->parent = parent_of_removed_node;
        if (parent_of_removed_node) {
            // parent_of_removed_node can be nullptr if removed_node
            // was the root node
            if (!parent_of_removed_node->left_child) {
                parent_of_removed_node->left_child = surviving_child_of_removed_node;
            } else {
                assert(!parent_of_removed_node->right_child);
                parent_of_removed_node->right_child = surviving_child_of_removed_node;
            }
        }

//        cout << "after update" << endl;
//        inorder_traversal(4);
    }
}

void MergeTree::inorder_traversal(int indentation_offset) const {
    cout << "Merge tree, read from left to right (90° rotated tree): "
         << endl;
    return root->inorder(indentation_offset, 0);
}
}
