function calculateResult(a: number, b: number, c: number) {
    const unusedValue = 123;

    if (a > 0) {        if (b > 0) {
            if (c > 0) {
                return a + b + c;
            } else {
                return a + b;
            }
        } else {
            if (c > 0) {
                return a + c;
            } else {
                return a;
            }
        }
    } else {
        if (b > 0) {
            return b + c;
        } else {
            return c;
        }
    }
}