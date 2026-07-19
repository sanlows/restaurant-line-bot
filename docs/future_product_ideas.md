# Future Product Ideas

## Assisted restaurant data completion

Status: idea only; not scheduled for implementation.

The multi-user web management direction is tracked separately in
[`web_management_plan.md`](web_management_plan.md).

### Current problem

When Facebook, Instagram, or another source blocks metadata parsing, the bot only
saves the original URL. The operator must then open Google Sheets and manually
fill in the restaurant name, category, and area.

### Product direction

Allow missing restaurant information to be completed from LINE instead of
requiring users to edit Google Sheets. A possible future flow is:

1. Save the original link immediately.
2. Attempt metadata extraction and Google Places matching automatically.
3. When confidence is high, fill in the restaurant information automatically.
4. When confidence is insufficient, accept a short restaurant hint in LINE and
   use it to search for the matching Google Maps place.
5. Store a confirmed Google Place ID so links from different sources can later
   be grouped under the same restaurant.

Possible later capabilities include restaurant deduplication, visited/wishlist
status, area and category search, random restaurant selection, and group voting.

### UX constraint

The full assisted flow could introduce too many steps and confuse beginner
users. It must not become the default multi-step experience without additional
design work.

Any future implementation should follow these principles:

- Keep the normal save action to one simple message.
- Do as much work automatically as possible.
- Never require users to understand Google Sheets fields or bot command syntax.
- Ask for clarification only when it materially improves the saved record.
- Prefer one short prompt or tappable choices over several typed commands.
- Allow users to skip completion and keep the URL-only record.
- Introduce advanced functions progressively instead of showing every option at
  once.

### Simplest candidate for a future experiment

After an automatic parse failure, keep the URL saved and show one optional,
plain-language prompt:

```text
已收藏。若要補上餐廳資料，直接回覆店名即可；也可以略過。
```

This should be tested with beginner users before expanding it into candidate
selection or a longer confirmation workflow.
