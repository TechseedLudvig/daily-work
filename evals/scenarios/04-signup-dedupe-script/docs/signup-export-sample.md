# Newsletter signup export: format and a sample

Invented data for an eval scenario.

The export is a CSV file, UTF-8, with a header row. Dates are YYYY-MM-DD.

```
email,name,signed_up,source
anna@example.com,Anna Berg,2026-03-02,web
Anna@Example.com ,Anna Berg,2026-01-15,event
bo@example.com,Bo Lind,2026-02-20,web
bo@example.com,Bo Lind,2026-02-20,web
cecilia.example.com,Cecilia Ek,2026-04-01,web
dan@example.com,Dan Holm,2026-05-05,partner
```

People sign up again at events and through partners, so the same person appears several
times, sometimes with the email typed differently.
