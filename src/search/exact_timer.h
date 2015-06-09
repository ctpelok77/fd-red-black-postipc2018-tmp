#ifndef EXACT_TIMER_H
#define EXACT_TIMER_H

#include "utilities.h"

#include <iosfwd>

#if OPERATING_SYSTEM == WINDOWS
#include <windows.h>
#endif

class ExactTimer {
    double last_start_clock;
    double collected_time;
    bool stopped;
#if OPERATING_SYSTEM == WINDOWS
    LARGE_INTEGER frequency;
    LARGE_INTEGER start_time;
#endif

    double current_clock() const;
public:
    ExactTimer();
    ~ExactTimer();
    double operator()() const;
    double stop();
    void resume();
    double reset();
};

std::ostream &operator<<(std::ostream &os, const ExactTimer &timer);

#endif
