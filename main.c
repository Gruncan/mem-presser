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
    size_t length = size * 1024 * 1024;

    struct sysinfo info;
    if (sysinfo(&info) != 0) {
        perror("sysinfo");
    }

    unsigned long freeRamStart = info.freeram;

    void *ptr;
    int count = 0;

    while (1) {
        if (sysinfo(&info) != 0) {
            perror("sysinfo");
            break;
        }

        if (info.freeram >= freeRamStart ) {
            length = (freeRamStart - info.freeram) / length;
        }

        ptr = malloc(length);
        if (ptr == NULL) {
            printf("Memory allocation failed after %d MB\n", count * 10);
            break;
        }
        memset(ptr, 0, length);

        count++;
        printf("Allocated %d MB\n", count * 10);

        usleep(100000); // 100 ms
    }

    return 0;
}
