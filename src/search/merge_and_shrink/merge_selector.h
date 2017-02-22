#ifndef MERGE_AND_SHRINK_MERGE_SELECTOR_H
#define MERGE_AND_SHRINK_MERGE_SELECTOR_H

#include <string>
#include <vector>

class TaskProxy;

namespace merge_and_shrink {
class FactoredTransitionSystem;
class MergeSelector {
protected:
    virtual std::string name() const = 0;
    virtual void dump_specific_options() const {}
    std::vector<std::pair<int, int>> compute_merge_candidates(
        FactoredTransitionSystem &fts,
        const std::vector<int> &indices_subset) const;
public:
    MergeSelector() = default;
    virtual ~MergeSelector() = default;
    virtual std::pair<int, int> select_merge(
        FactoredTransitionSystem &fts,
        const std::vector<int> &indices_subset = std::vector<int>()) const = 0;
    virtual void initialize(const TaskProxy &task_proxy) = 0;
    void dump_options() const;

    virtual bool requires_init_distances() const {
        return false;
    }

    virtual bool requires_goal_distances() const {
        return false;
    }
};
}

#endif
