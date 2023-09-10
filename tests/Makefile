CFLAGS = -Werror -Wall -Wextra -Wpedantic -std=c17 -D_POSIX_C_SOURCE=199309L
OFLAGS = -O1

data.json : dump
	./dump > data.json

dump : test_02.c
	$(CC) $(CFLAGS) $(OFLAGS) $< -o $@
