
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <string.h>


#define LOG_FILE "memory_usage.log"
#define SLEEP_TIME 1000 // Microseconds


void log_memory_usage() {
    char buffer[256];
    int memory_used = 0;
    int total_mem = 0, free_mem = 0, buffers = 0, cached = 0;

    FILE *meminfo = fopen("/proc/meminfo", "r");
    if (meminfo == NULL) {
        perror("Failed to open /proc/meminfo!");
        return;
    }

    while (fgets(buffer, sizeof(buffer), meminfo)) {
        if (sscanf(buffer, "MemTotal: %d kB", &total_mem) == 1 ||
            sscanf(buffer, "MemFree: %d kB", &free_mem) == 1 ||
            sscanf(buffer, "Buffers: %d kB", &buffers) == 1 ||
            sscanf(buffer, "Cached: %d kB", &cached) == 1) {
            if (total_mem > 0 && free_mem > 0 && buffers > 0 && cached > 0)
                break;
            }
    }
    fclose(meminfo);

    struct timespec ts;
    char time_buffer[32];

    clock_gettime(CLOCK_REALTIME, &ts);
    struct tm *tm_info = localtime(&ts.tv_sec);

    strftime(time_buffer, sizeof(time_buffer), "%Y-%m-%d %H:%M:%S", tm_info);
    snprintf(time_buffer + strlen(time_buffer), sizeof(time_buffer) - strlen(time_buffer), ".%03ld", ts.tv_nsec / 1000000);

    FILE *log_file = fopen(LOG_FILE, "a");
    if (log_file == NULL) {
        perror("Failed to open log file!");
        return;
    }
    fprintf(log_file, "%s - %d kB\n", time_buffer, memory_used);
    fclose(log_file);

}


int main() {
    while (1) {
        log_memory_usage();
        usleep(SLEEP_TIME);
    }
    return 0;
}