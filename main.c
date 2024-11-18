#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/sysinfo.h>

int main(int argc, char *argv[]){

    if (argc <= 1 || argc > 2) {
        printf("Usage: %s [size in mb]\n", argv[0]);
        return 1;
    }

    int size = atoi(argv[1]);
    unsigned long length = size * 1024 * 1024;

    struct sysinfo info;
    if (sysinfo(&info) != 0) {
        perror("sysinfo");
    }

    unsigned long long freeRamStart = info.freeram;

    void **ptrs = malloc(256 * sizeof(void*));
    int count = 0;
    int allocation_times = 0;

    unsigned long l2 = length;

    while (1) {

        ptrs[allocation_times] = malloc(l2);
        if (ptrs[allocation_times] == NULL) {
            printf("Memory allocation failed after %d MB\n", count * 10);
            break;
        }
        memset(ptrs[allocation_times], 0, l2);

        printf("Allocated %d\n", allocation_times);
        allocation_times++;

        usleep(100000); // 100 ms

        if (sysinfo(&info) != 0) {
            perror("sysinfo");
            break;
        }


        if ((double) info.freeram <= 0.3 * (double) freeRamStart && count == 0) {
            l2 /= 2;
            count++;
        }else if ((double) info.freeram <= 0.2 * (double) freeRamStart && count == 1) {
            l2 /= 2;
            count++;
        }else if ((double) info.freeram <= 0.1 * (double) freeRamStart && count == 2) {
            for(int i = 0; i < allocation_times; i++) {
                free(ptrs[i]);
            }
            allocation_times = 0;
            count = 0;
            l2 = length;
        }

    }

    return 0;
}
