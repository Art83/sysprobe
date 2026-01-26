CC = gcc
CFLAGS = -Wall -Wextra -O2 -Iinclude
PREFIX = /usr/local
BINDIR=$(PREFIX)/bin
SRC=$(wildcard source/*.c)
TARGET=sysprobe

.PHONY: all install uninstall clean

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

install: $(TARGET)
	mkdir -p $(BINDIR)
	cp $(TARGET) $(BINDIR)/

uninstall:
	rm -f $(BINDIR)/$(TARGET)

clean:
	rm -f $(TARGET)



