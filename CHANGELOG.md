# Change Log

## [v1.0.5](https://github.com/stphivos/django-mock-queries/tree/v1.0.5) (2017-11-30)
[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.4...v1.0.5)

## [v1.0.4](https://github.com/stphivos/django-mock-queries/tree/v1.0.4) (2017-11-30)
[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.2...v1.0.4)

**Fixed bugs:**

- Support filtering on a values list subquery. [\#54](https://github.com/stphivos/django-mock-queries/pull/54) ([donkirkby](https://github.com/donkirkby))

**Merged pull requests:**

- MockSet earliest/latest fields args [\#57](https://github.com/stphivos/django-mock-queries/pull/57) ([stphivos](https://github.com/stphivos))
- Not obligatory field parameter in latest and earliest query function [\#56](https://github.com/stphivos/django-mock-queries/pull/56) ([grabekm90](https://github.com/grabekm90))
- Fix a missed model parameter for MockSet in ModelMocker [\#55](https://github.com/stphivos/django-mock-queries/pull/55) ([grabekm90](https://github.com/grabekm90))

## [v1.0.2](https://github.com/stphivos/django-mock-queries/tree/v1.0.2) (2017-10-16)
[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v1.0.0...v1.0.2)

**Merged pull requests:**

- Fix hardcoded requirement to six library [\#53](https://github.com/stphivos/django-mock-queries/pull/53) ([stphivos](https://github.com/stphivos))

## [v1.0.0](https://github.com/stphivos/django-mock-queries/tree/v1.0.0) (2017-10-15)
[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v0.0.16...v1.0.0)

**Closed issues:**

- Model.objects.create can't take an instance parameter [\#50](https://github.com/stphivos/django-mock-queries/issues/50)
- Q objects with negation [\#48](https://github.com/stphivos/django-mock-queries/issues/48)

**Merged pull requests:**

- Verify support of Django 1.11 [\#52](https://github.com/stphivos/django-mock-queries/pull/52) ([stphivos](https://github.com/stphivos))
- Use function find\_field\_names to determine appropriate field names fo… [\#51](https://github.com/stphivos/django-mock-queries/pull/51) ([stphivos](https://github.com/stphivos))
- Add support for Q objects with negation [\#49](https://github.com/stphivos/django-mock-queries/pull/49) ([stphivos](https://github.com/stphivos))
- Added missing lookups [\#47](https://github.com/stphivos/django-mock-queries/pull/47) ([szykin](https://github.com/szykin))
- dates\(\) and datetimes\(\) support [\#46](https://github.com/stphivos/django-mock-queries/pull/46) ([szykin](https://github.com/szykin))
- Feature/range requirements [\#45](https://github.com/stphivos/django-mock-queries/pull/45) ([stphivos](https://github.com/stphivos))
- Update model-mommy req [\#44](https://github.com/stphivos/django-mock-queries/pull/44) ([orf](https://github.com/orf))

## [v0.0.16](https://github.com/stphivos/django-mock-queries/tree/v0.0.16) (2017-03-14)
[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v0.0.15...v0.0.16)

**Merged pull requests:**

- Upload v0.0.16 to pypi [\#43](https://github.com/stphivos/django-mock-queries/pull/43) ([stphivos](https://github.com/stphivos))
- Comparisons: regex, iregex, date, datetime rework. [\#42](https://github.com/stphivos/django-mock-queries/pull/42) ([szykin](https://github.com/szykin))
- Fix one-to-many field lookup to use model name [\#41](https://github.com/stphivos/django-mock-queries/pull/41) ([stphivos](https://github.com/stphivos))

## [v0.0.15](https://github.com/stphivos/django-mock-queries/tree/v0.0.15) (2017-03-06)
[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v0.0.14...v0.0.15)

**Merged pull requests:**

- Update missing qs methods, lookups, aggregations. [\#39](https://github.com/stphivos/django-mock-queries/pull/39) ([stphivos](https://github.com/stphivos))
- Add support for nested fields to values and values\_list [\#38](https://github.com/stphivos/django-mock-queries/pull/38) ([stphivos](https://github.com/stphivos))
- Add support for aggregate on related fields [\#37](https://github.com/stphivos/django-mock-queries/pull/37) ([stphivos](https://github.com/stphivos))
- MockOptions, get\_or\_create\_with defaults [\#36](https://github.com/stphivos/django-mock-queries/pull/36) ([szykin](https://github.com/szykin))
- Add docs todo, remove completed decorators todo. [\#35](https://github.com/stphivos/django-mock-queries/pull/35) ([stphivos](https://github.com/stphivos))
- Add some quirky queries supported by Django: pk is in a subquery and child is equal. [\#34](https://github.com/stphivos/django-mock-queries/pull/34) ([donkirkby](https://github.com/donkirkby))
- Raise specific DoesNotExist exception for the model. [\#32](https://github.com/stphivos/django-mock-queries/pull/32) ([donkirkby](https://github.com/donkirkby))
- Add decorators for unified method patching/replacement [\#31](https://github.com/stphivos/django-mock-queries/pull/31) ([stphivos](https://github.com/stphivos))
- \_meta, values\(\), values\_list\(\) [\#30](https://github.com/stphivos/django-mock-queries/pull/30) ([szykin](https://github.com/szykin))
- Add mocked\_relations decorator for all related models. [\#28](https://github.com/stphivos/django-mock-queries/pull/28) ([donkirkby](https://github.com/donkirkby))

## [v0.0.14](https://github.com/stphivos/django-mock-queries/tree/v0.0.14) (2016-12-15)
[Full Changelog](https://github.com/stphivos/django-mock-queries/compare/v0.0.13...v0.0.14)

**Merged pull requests:**

- Upload v0.0.14 to PyPI [\#25](https://github.com/stphivos/django-mock-queries/pull/25) ([stphivos](https://github.com/stphivos))
- Feature/aggregate multi params [\#24](https://github.com/stphivos/django-mock-queries/pull/24) ([szykin](https://github.com/szykin))
- Mock django db [\#23](https://github.com/stphivos/django-mock-queries/pull/23) ([donkirkby](https://github.com/donkirkby))
- added spec\_set to MockModel [\#22](https://github.com/stphivos/django-mock-queries/pull/22) ([szykin](https://github.com/szykin))
- Mocked querysets aggregation now handles None values. [\#21](https://github.com/stphivos/django-mock-queries/pull/21) ([szykin](https://github.com/szykin))
- Complete test coverage by testing with a real Django Q object. [\#19](https://github.com/stphivos/django-mock-queries/pull/19) ([donkirkby](https://github.com/donkirkby))
- Raise an error when there's a typo in a queryset's field name. [\#18](https://github.com/stphivos/django-mock-queries/pull/18) ([donkirkby](https://github.com/donkirkby))
- Update py-test requirement versions and add pip-tools [\#15](https://github.com/stphivos/django-mock-queries/pull/15) ([stphivos](https://github.com/stphivos))
- Skipfieldfix [\#14](https://github.com/stphivos/django-mock-queries/pull/14) ([donkirkby](https://github.com/donkirkby))
- Version 3 of flake8 contains breaking changes, so pin requirement. [\#13](https://github.com/stphivos/django-mock-queries/pull/13) ([donkirkby](https://github.com/donkirkby))

## [v0.0.13](https://github.com/stphivos/django-mock-queries/tree/v0.0.13) (2016-06-08)
**Merged pull requests:**

- Add distinct\(\) to MockSet. [\#12](https://github.com/stphivos/django-mock-queries/pull/12) ([donkirkby](https://github.com/donkirkby))
- Add first\(\) and last\(\) to MockSet. [\#11](https://github.com/stphivos/django-mock-queries/pull/11) ([donkirkby](https://github.com/donkirkby))
- Add support for values list and individual attrs projection [\#10](https://github.com/stphivos/django-mock-queries/pull/10) ([stphivos](https://github.com/stphivos))
- Use generic mock\_set clone for init [\#9](https://github.com/stphivos/django-mock-queries/pull/9) ([stphivos](https://github.com/stphivos))
- Add order\_by\(\) to MockSet\(\) [\#8](https://github.com/stphivos/django-mock-queries/pull/8) ([donkirkby](https://github.com/donkirkby))
- Add exclude\(\) to MockSet [\#7](https://github.com/stphivos/django-mock-queries/pull/7) ([donkirkby](https://github.com/donkirkby))
- In and isnull [\#6](https://github.com/stphivos/django-mock-queries/pull/6) ([donkirkby](https://github.com/donkirkby))
- django-rest-framework serializer assert function [\#5](https://github.com/stphivos/django-mock-queries/pull/5) ([stphivos](https://github.com/stphivos))
- Test remaining crud functions and exception scenarios [\#4](https://github.com/stphivos/django-mock-queries/pull/4) ([stphivos](https://github.com/stphivos))
- Test query aggregate, create and get functionality [\#3](https://github.com/stphivos/django-mock-queries/pull/3) ([stphivos](https://github.com/stphivos))
- Fix and test query filtering by q objects [\#2](https://github.com/stphivos/django-mock-queries/pull/2) ([stphivos](https://github.com/stphivos))
- Fix/remove pytest ini [\#1](https://github.com/stphivos/django-mock-queries/pull/1) ([stphivos](https://github.com/stphivos))



\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*