with open('static/css/tailwind.css', 'r') as f:
    content = f.read()

checks = [
    'h-8', 'h-9', 'h-10', 'h-11', 'h-14',
    'px-4', 'px-6', 'py-8', 'py-12',
    'gap-2', 'gap-3', 'gap-4', 'gap-6',
    'p-4', 'p-6', 'p-8', 'p-12',
    'mb-4', 'mt-4', 'mt-1', 'mt-2',
    'space-y-6', 'space-y-8',
    'sm:grid-cols-2', 'md:grid-cols', 'lg:grid-cols',
    'rounded-\\[22px\\]', 'rounded-\\[24px\\]',
    'shadow-xs', 'text-white', 'bg-white',
    'font-bold', 'font-semibold', 'font-medium',
    'tracking-tight', 'leading-snug', 'leading-relaxed',
    'md:flex-row', 'sm:flex-row', 'lg:items-center',
]

missing = []
ok = []
for c in checks:
    if c in content:
        ok.append(c)
    else:
        missing.append(c)

print("PRESENT:", len(ok))
print("MISSING:", len(missing))
for m in missing:
    print("  MISSING:", m)
