/*
 * LearnLoop sketch engine (Reader RW5d P2, docs/specs/spec_reader_show_me_figures_v1.md §9).
 *
 * QuickJS-ng, amalgamated and pinned (engine.lock.json), compiled to one
 * WebAssembly reactor that both hosts run byte for byte: the desktop's Web
 * Worker (sketchEngine.ts) and the sidecar's wasmtime runner
 * (learnloop.figures.sketch_engine). The same bytes in both is what makes a
 * drawn value equal a verified value exactly.
 *
 * The ABI is data only. A host copies JSON (or the program's source) into the
 * one input buffer and calls an operation; the result is JSON text (or an
 * error message) in the output buffer. The program sees nothing but its
 * arguments and `rand()`: no host bindings, no Date, no Math.random, no
 * performance, no RegExp, Proxy, Promise or WeakRef, and the only imports are
 * the WASI functions wasi-libc links, which every host answers with a
 * deny-all shim (no files, clock, randomness, environment or network).
 *
 * State never leaves the engine: init() keeps its result, step() replaces
 * it, view() and probes() read it. Each entry point is reseeded from (seed,
 * phase, step index) before it runs, so a run's values depend only on the
 * parameters, the seed and the step count, never on how a host chunked its
 * calls. Each entry-point invocation gets the same work budget (QuickJS
 * interrupt ticks, deterministic), so the cap is identical in every host.
 *
 * Limits are compiled in (sk_limits reports them) so no host can run the
 * engine under different caps than another.
 */

#include "quickjs-amalgam.c"

#define SK_EXPORT(name) __attribute__((export_name(#name)))

/* Guardrails (keep): machine safety and interactivity, never model parameters.
 * Mirrored as SKETCH_* constants in learnloop.figures.sketch_engine and
 * sketchEngine.ts; tests assert they equal sk_limits(). */
#define SK_MEMORY_BYTES (64u * 1024u * 1024u)   /* SKETCH_MEMORY_BYTES */
#define SK_STACK_BYTES (192u * 1024u)           /* JS recursion depth guard (shadow stack) */
#define SK_TICKS_PER_CALL 48u                   /* SKETCH_FUEL_PER_CALL: interrupt ticks per entry-point call */
#define SK_MAX_OUTPUT (4u * 1024u * 1024u)      /* largest result text */
#define SK_MAX_MESSAGE 400u                     /* largest error message */

enum {
    SK_OK = 0,
    SK_ERROR = 1,      /* the program threw */
    SK_WORK = 2,       /* the work cap */
    SK_MEMORY = 3,     /* the memory cap */
    SK_STACK = 4,      /* recursion too deep */
    SK_NOPROGRAM = 5,  /* nothing loaded, or an entry point is missing */
    SK_OUTPUT = 6,     /* a result that is too large or not representable */
    SK_INPUT = 7,      /* the host's input is not valid JSON */
};

enum { PHASE_LOAD = 0, PHASE_INIT = 1, PHASE_STEP = 2, PHASE_VIEW = 3, PHASE_PROBES = 4 };

static JSRuntime *sk_rt;
static JSContext *sk_ctx;
static JSValue sk_state;
static JSValue sk_fn[5];       /* indexed by phase: init, step, view, probes */
static JSValue sk_stringify;
static int sk_loaded;

static uint8_t *sk_in;
static uint32_t sk_in_cap;
static char *sk_out;
static uint32_t sk_out_len;
static uint32_t sk_out_cap;

static int64_t sk_ticks_left;
static int sk_interrupted;
static uint32_t sk_seed;
static uint64_t sk_rng;

/* ------------------------------------------------------------------ buffers */

SK_EXPORT(sk_buffer) uint8_t *sk_buffer(uint32_t size)
{
    if (size + 1 > sk_in_cap) {
        uint8_t *grown = realloc(sk_in, size + 1);
        if (!grown)
            return NULL;
        sk_in = grown;
        sk_in_cap = size + 1;
    }
    return sk_in;
}

SK_EXPORT(sk_output_ptr) const char *sk_output_ptr(void) { return sk_out ? sk_out : ""; }
SK_EXPORT(sk_output_len) uint32_t sk_output_len(void) { return sk_out_len; }

static int out_set(const char *text, size_t len)
{
    if (len > SK_MAX_OUTPUT)
        return -1;
    if (len + 1 > sk_out_cap) {
        char *grown = realloc(sk_out, len + 1);
        if (!grown)
            return -1;
        sk_out = grown;
        sk_out_cap = (uint32_t)len + 1;
    }
    memcpy(sk_out, text, len);
    sk_out[len] = 0;
    sk_out_len = (uint32_t)len;
    return 0;
}

static void out_message(const char *text)
{
    size_t len = strlen(text);
    if (len > SK_MAX_MESSAGE) {
        len = SK_MAX_MESSAGE;
        /* never cut a UTF-8 sequence in half */
        while (len > 0 && (((unsigned char)text[len]) & 0xC0) == 0x80)
            len--;
    }
    out_set(text, len);
}

SK_EXPORT(sk_limits) uint32_t sk_limits(void)
{
    char text[256];
    int n = snprintf(text, sizeof text,
                     "{\"memory_bytes\":%u,\"stack_bytes\":%u,\"ticks_per_call\":%u,"
                     "\"max_output\":%u,\"interrupt_counter\":%d,\"quickjs\":\"%s\"}",
                     SK_MEMORY_BYTES, SK_STACK_BYTES, SK_TICKS_PER_CALL, SK_MAX_OUTPUT,
                     JS_INTERRUPT_COUNTER_INIT, JS_GetVersion());
    out_set(text, (size_t)n);
    return SK_OK;
}

/* ----------------------------------------------------------- rand(), seeded */

static uint64_t splitmix64(uint64_t *s)
{
    uint64_t z = (*s += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static void reseed(uint32_t phase, uint64_t index)
{
    uint64_t s = ((uint64_t)sk_seed << 32) ^ ((uint64_t)phase << 8) ^ 0x5EEDu;
    uint64_t mixed = splitmix64(&s) ^ (index * 0xD1B54A32D192ED03ULL);
    sk_rng = mixed;
    (void)splitmix64(&sk_rng);
}

static JSValue js_sketch_rand(JSContext *ctx, JSValueConst this_val, int argc, JSValueConst *argv)
{
    (void)this_val; (void)argc; (void)argv;
    uint64_t bits = splitmix64(&sk_rng) >> 11;
    return js_float64((double)bits * 0x1.0p-53);
}

/* ------------------------------------------------------- the work budget */

static int sk_interrupt(JSRuntime *rt, void *opaque)
{
    (void)rt; (void)opaque;
    if (--sk_ticks_left < 0) {
        sk_interrupted = 1;
        return 1;
    }
    return 0;
}

static void begin_call(void)
{
    JS_UpdateStackTop(sk_rt);
    sk_ctx->interrupt_counter = JS_INTERRUPT_COUNTER_INIT;
    sk_ticks_left = SK_TICKS_PER_CALL;
    sk_interrupted = 0;
}

/* The pending exception as a status, with its message in the output. */
static int fail_from_exception(const char *where)
{
    JSValue exception = JS_GetException(sk_ctx);
    int status = SK_ERROR;
    const char *message = NULL;
    char text[SK_MAX_MESSAGE + 64];
    if (sk_interrupted) {
        status = SK_WORK;
    } else {
        message = JS_ToCString(sk_ctx, exception);
        if (message && strstr(message, "out of memory"))
            status = SK_MEMORY;
        else if (message && strstr(message, "Maximum call stack size exceeded"))
            status = SK_STACK;
        else if (!message)
            status = SK_MEMORY; /* converting the exception itself ran out of memory */
    }
    if (status == SK_WORK)
        snprintf(text, sizeof text, "%s: used its whole work budget (a loop that does not end, or too much work)", where);
    else if (status == SK_MEMORY)
        snprintf(text, sizeof text, "%s: used more memory than a sketch may", where);
    else if (status == SK_STACK)
        snprintf(text, sizeof text, "%s: recursion too deep", where);
    else
        snprintf(text, sizeof text, "%s: %s", where, message ? message : "an error");
    if (message)
        JS_FreeCString(sk_ctx, message);
    JS_FreeValue(sk_ctx, exception);
    out_message(text);
    if (status != SK_ERROR)
        JS_RunGC(sk_rt);
    return status;
}

/* ------------------------------------------------------------- lifecycle */

static void unload(void)
{
    if (sk_ctx) {
        JS_FreeValue(sk_ctx, sk_state);
        for (int i = 0; i < 5; i++)
            JS_FreeValue(sk_ctx, sk_fn[i]);
        JS_FreeValue(sk_ctx, sk_stringify);
        JS_FreeContext(sk_ctx);
        sk_ctx = NULL;
    }
    if (sk_rt) {
        JS_FreeRuntime(sk_rt);
        sk_rt = NULL;
    }
    sk_state = JS_UNDEFINED;
    for (int i = 0; i < 5; i++)
        sk_fn[i] = JS_UNDEFINED;
    sk_stringify = JS_UNDEFINED;
    sk_loaded = 0;
}

/* Results cross as JSON: a non-finite number becomes the string "NaN",
 * "Infinity" or "-Infinity", so a host's validator names it instead of
 * reading null. Captured before the program runs (it may replace JSON). */
static const char HARNESS[] =
    "(function () {\n"
    "  var stringify = JSON.stringify, finite = Number.isFinite;\n"
    "  function replacer(key, value) {\n"
    "    if (typeof value === 'number' && !finite(value))\n"
    "      return value !== value ? 'NaN' : (value > 0 ? 'Infinity' : '-Infinity');\n"
    "    return value;\n"
    "  }\n"
    "  return function (value) {\n"
    "    var text = stringify(value, replacer);\n"
    "    return text === undefined ? 'null' : text;\n"
    "  };\n"
    "})()";

static const char *const ENTRY_NAMES[5] = {NULL, "init", "step", "view", "probes"};

/* Load a program (its source is in the input buffer). A fresh runtime every
 * time: nothing survives from an earlier program. */
SK_EXPORT(sk_load) int32_t sk_load(uint32_t len)
{
    unload();
    sk_out_len = 0;
    if (!sk_in || len + 1 > sk_in_cap) {
        out_message("load: no program");
        return SK_NOPROGRAM;
    }
    sk_in[len] = 0;
    sk_rt = JS_NewRuntime();
    if (!sk_rt) {
        out_message("load: the engine could not start");
        return SK_MEMORY;
    }
    JS_SetMemoryLimit(sk_rt, SK_MEMORY_BYTES);
    JS_SetMaxStackSize(sk_rt, SK_STACK_BYTES);
    JS_SetInterruptHandler(sk_rt, sk_interrupt, NULL);
    sk_ctx = JS_NewContextRaw(sk_rt);
    if (!sk_ctx || JS_AddIntrinsicBaseObjects(sk_ctx) || JS_AddIntrinsicEval(sk_ctx) ||
        JS_AddIntrinsicJSON(sk_ctx) || JS_AddIntrinsicMapSet(sk_ctx) || JS_AddIntrinsicTypedArrays(sk_ctx)) {
        unload();
        out_message("load: the engine could not start");
        return SK_MEMORY;
    }
    /* No clock reached the context: its hash seed and Math.random state are fixed. */
    sk_ctx->random_state = 0x2545F4914F6CDD1DULL;
    sk_ctx->hash_seed = 0x9E3779B9u;
    sk_state = JS_UNDEFINED;
    for (int i = 0; i < 5; i++)
        sk_fn[i] = JS_UNDEFINED;
    sk_stringify = JS_UNDEFINED;

    JSValue global = JS_GetGlobalObject(sk_ctx);
    /* Math.random is absent: rand() is the only randomness, seeded by the host. */
    JSValue math = JS_GetPropertyStr(sk_ctx, global, "Math");
    JSAtom random = JS_NewAtom(sk_ctx, "random");
    JS_DeleteProperty(sk_ctx, math, random, 0);
    JS_FreeAtom(sk_ctx, random);
    JS_FreeValue(sk_ctx, math);
    /* No deferred work and no shared memory: queueMicrotask's jobs would never
     * run (the host never drains the job queue) and SharedArrayBuffer has no
     * other thread to share with; both are removed so nothing pretends. */
    static const char *const REMOVED[] = {"queueMicrotask", "SharedArrayBuffer", "Atomics"};
    for (size_t i = 0; i < sizeof REMOVED / sizeof REMOVED[0]; i++) {
        JSAtom name = JS_NewAtom(sk_ctx, REMOVED[i]);
        JS_DeleteProperty(sk_ctx, global, name, 0);
        JS_FreeAtom(sk_ctx, name);
    }
    JS_SetPropertyStr(sk_ctx, global, "rand", JS_NewCFunction(sk_ctx, js_sketch_rand, "rand", 0));

    begin_call();
    sk_stringify = JS_Eval(sk_ctx, HARNESS, sizeof HARNESS - 1, "<harness>", JS_EVAL_TYPE_GLOBAL);
    if (JS_IsException(sk_stringify)) {
        JS_FreeValue(sk_ctx, global);
        int status = fail_from_exception("load");
        unload();
        return status;
    }

    sk_seed = 0;
    reseed(PHASE_LOAD, 0);
    begin_call();
    JSValue result = JS_Eval(sk_ctx, (const char *)sk_in, len, "<sketch>", JS_EVAL_TYPE_GLOBAL);
    if (JS_IsException(result)) {
        JS_FreeValue(sk_ctx, global);
        int status = fail_from_exception("load");
        unload();
        return status;
    }
    JS_FreeValue(sk_ctx, result);

    char found[128];
    int n = snprintf(found, sizeof found, "{");
    for (int phase = PHASE_INIT; phase <= PHASE_PROBES; phase++) {
        JSValue fn = JS_GetPropertyStr(sk_ctx, global, ENTRY_NAMES[phase]);
        int is_fn = !JS_IsException(fn) && JS_IsFunction(sk_ctx, fn);
        if (JS_IsException(fn))
            JS_FreeValue(sk_ctx, JS_GetException(sk_ctx));
        if (is_fn) {
            sk_fn[phase] = fn;
        } else {
            JS_FreeValue(sk_ctx, fn);
            sk_fn[phase] = JS_UNDEFINED;
        }
        n += snprintf(found + n, sizeof found - (size_t)n, "%s\"%s\":%s", phase == PHASE_INIT ? "" : ",",
                      ENTRY_NAMES[phase], is_fn ? "true" : "false");
    }
    snprintf(found + n, sizeof found - (size_t)n, "}");
    JS_FreeValue(sk_ctx, global);
    out_set(found, strlen(found));
    sk_loaded = 1;
    return SK_OK;
}

/* ------------------------------------------------------------ operations */

static int parse_input(uint32_t len, JSValue *value, const char *where)
{
    char text[96];
    if (!sk_in || len + 1 > sk_in_cap) {
        snprintf(text, sizeof text, "%s: no input", where);
        out_message(text);
        return SK_INPUT;
    }
    sk_in[len] = 0;
    begin_call();
    *value = JS_ParseJSON(sk_ctx, (const char *)sk_in, len, "<input>");
    if (JS_IsException(*value)) {
        JS_FreeValue(sk_ctx, JS_GetException(sk_ctx));
        snprintf(text, sizeof text, "%s: the host's input is not JSON", where);
        out_message(text);
        return SK_INPUT;
    }
    return SK_OK;
}

static int need(int phase)
{
    char text[96];
    if (!sk_loaded) {
        out_message("no program is loaded");
        return SK_NOPROGRAM;
    }
    if (JS_IsUndefined(sk_fn[phase])) {
        snprintf(text, sizeof text, "the program defines no %s()", ENTRY_NAMES[phase]);
        out_message(text);
        return SK_NOPROGRAM;
    }
    return SK_OK;
}

/* init(p, seed): input is the parameters' JSON object. */
SK_EXPORT(sk_init) int32_t sk_init(uint32_t len, uint32_t seed)
{
    int status = need(PHASE_INIT);
    if (status)
        return status;
    JSValue params;
    if ((status = parse_input(len, &params, "init")))
        return status;
    sk_seed = seed;
    JS_FreeValue(sk_ctx, sk_state);
    sk_state = JS_UNDEFINED;
    JSValue args[2] = {params, JS_NewUint32(sk_ctx, seed)};
    reseed(PHASE_INIT, 0);
    begin_call();
    JSValue result = JS_Call(sk_ctx, sk_fn[PHASE_INIT], JS_UNDEFINED, 2, args);
    JS_FreeValue(sk_ctx, params);
    if (JS_IsException(result))
        return fail_from_exception("init");
    sk_state = result;
    sk_out_len = 0;
    return SK_OK;
}

/* step(state, p, dt), `count` times from step index `index`: input is
 * {"p": {...}, "dt": number}. Each step is its own call: its own reseed
 * (seed, index) and its own work budget, and a fresh copy of p. */
SK_EXPORT(sk_step) int32_t sk_step(uint32_t len, uint32_t index, uint32_t count)
{
    int status = need(PHASE_STEP);
    if (status)
        return status;
    JSValue input;
    if ((status = parse_input(len, &input, "step")))
        return status;
    JSValue dt = JS_GetPropertyStr(sk_ctx, input, "dt");
    JSValue p_value = JS_GetPropertyStr(sk_ctx, input, "p");
    JSValue p_text = JS_JSONStringify(sk_ctx, p_value, JS_UNDEFINED, JS_UNDEFINED);
    JS_FreeValue(sk_ctx, p_value);
    JS_FreeValue(sk_ctx, input);
    size_t p_len = 0;
    const char *p_chars = JS_IsException(p_text) ? NULL : JS_ToCStringLen(sk_ctx, &p_len, p_text);
    JS_FreeValue(sk_ctx, p_text);
    if (!p_chars) {
        JS_FreeValue(sk_ctx, dt);
        out_message("step: the host's input is not JSON");
        return SK_INPUT;
    }
    char where[48];
    status = SK_OK;
    for (uint32_t i = 0; i < count; i++) {
        snprintf(where, sizeof where, "step %u", index + i);
        begin_call();
        JSValue params = JS_ParseJSON(sk_ctx, p_chars, p_len, "<input>");
        if (JS_IsException(params)) {
            status = fail_from_exception(where);
            break;
        }
        JSValue args[3] = {sk_state, params, dt};
        reseed(PHASE_STEP, (uint64_t)index + i);
        begin_call();
        JSValue result = JS_Call(sk_ctx, sk_fn[PHASE_STEP], JS_UNDEFINED, 3, args);
        JS_FreeValue(sk_ctx, params);
        if (JS_IsException(result)) {
            status = fail_from_exception(where);
            break;
        }
        JS_FreeValue(sk_ctx, sk_state);
        sk_state = result;
    }
    JS_FreeCString(sk_ctx, p_chars);
    JS_FreeValue(sk_ctx, dt);
    if (status == SK_OK)
        sk_out_len = 0;
    return status;
}

/* view(state, p) or probes(state, p) at step index `index`: input is the
 * parameters; the result is JSON text in the output buffer. */
static int32_t read_entry(int phase, uint32_t len, uint32_t index)
{
    int status = need(phase);
    if (status)
        return status;
    const char *name = ENTRY_NAMES[phase];
    JSValue params;
    if ((status = parse_input(len, &params, name)))
        return status;
    JSValue args[2] = {sk_state, params};
    reseed((uint32_t)phase, index);
    begin_call();
    JSValue result = JS_Call(sk_ctx, sk_fn[phase], JS_UNDEFINED, 2, args);
    JS_FreeValue(sk_ctx, params);
    if (JS_IsException(result))
        return fail_from_exception(name);
    /* Serializing is part of the same call and budget (getters and toJSON run here). */
    JSValue text = JS_Call(sk_ctx, sk_stringify, JS_UNDEFINED, 1, (JSValueConst *)&result);
    JS_FreeValue(sk_ctx, result);
    if (JS_IsException(text))
        return fail_from_exception(name);
    size_t text_len = 0;
    const char *chars = JS_ToCStringLen(sk_ctx, &text_len, text);
    JS_FreeValue(sk_ctx, text);
    if (!chars) {
        JS_FreeValue(sk_ctx, JS_GetException(sk_ctx));
        out_message("the result could not be read");
        return SK_OUTPUT;
    }
    int written = out_set(chars, text_len);
    JS_FreeCString(sk_ctx, chars);
    if (written) {
        char message[96];
        snprintf(message, sizeof message, "%s: the result is too large", name);
        out_message(message);
        return SK_OUTPUT;
    }
    return SK_OK;
}

SK_EXPORT(sk_view) int32_t sk_view(uint32_t len, uint32_t index) { return read_entry(PHASE_VIEW, len, index); }
SK_EXPORT(sk_probes) int32_t sk_probes(uint32_t len, uint32_t index) { return read_entry(PHASE_PROBES, len, index); }

SK_EXPORT(sk_unload) void sk_unload(void) { unload(); }
