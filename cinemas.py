import argparse
import requests
import re

from bs4 import BeautifulSoup

AFISHA_RU_URL = "http://www.afisha.ru/msk/schedule_cinema/"
KINOPOISK_RU_URL = "https://www.kinopoisk.ru/index.php"


def get_afisha_movies_base_inform():
    response = requests.get(AFISHA_RU_URL)
    parsed_html = BeautifulSoup(response.text, 'html.parser')
    movie_list = parsed_html.find(class_='b-theme-schedule m-schedule-with-collapse')\
                            .find_all(class_='object s-votes-hover-area collapsed')
    if movie_list is None:
        print("No movies on afisha page!")
        exit()
    return movie_list


def parse_list_tags_movies_afisha(movie_list_tags):
    movie_dict = {}
    for movie_tag in movie_list_tags:
        movie_name = movie_tag.find(class_='m-disp-table').find("a").get_text()
        cinema_list = movie_tag.find('table').find_all(class_="b-td-item")
        year = get_afisha_movie_year(movie_tag)

        movie_dict[movie_name] = {'number_of_cinemas': len(cinema_list),
                                  'year': year,
                                  'rating': None,
                                  'users': None}
    return movie_dict


def fetch_movie_info(movie_afisha_dict):
    for movie_name_afish in movie_afisha_dict.keys():
        payload = {'kp_query': movie_name_afish}
        response = requests.get(KINOPOISK_RU_URL, params=payload)

        parsed_html = BeautifulSoup(response.content, 'html.parser')
        movies_kinopoisk_tags = parsed_html.find_all(class_='search_results')

        for movie_kinopoisk_tags in movies_kinopoisk_tags:
            movie_names_kinopoisk = movie_kinopoisk_tags.find_all("p", class_='name')

            for current_movie_kinopoisk in movie_names_kinopoisk:
                movie_name_kinopoisk_without_punctuation = re.sub(r'[^\w\d]', ' ', current_movie_kinopoisk.find('a')
                                                                                                          .get_text())
                movie_name_afisha_without_punctuation = re.sub(r'[^\w\d]', ' ', movie_name_afish)

                if movie_name_afisha_without_punctuation.lower() != movie_name_kinopoisk_without_punctuation.lower():
                    continue

                year = movie_kinopoisk_tags.find(class_='name').find(class_='year')
                if year is None:
                    continue

                year = year.get_text()
                if year != movie_afisha_dict[movie_name_afish]['year']:
                    continue

                rating_tag = movie_kinopoisk_tags.find(class_='rating')
                if rating_tag is not None:
                    title = rating_tag['title'].replace(u'\xa0', '')
                    rating, number_of_user = title.split(" ")
                    movie_afisha_dict[movie_name_afish]['rating'] = rating
                    movie_afisha_dict[movie_name_afish]['users'] = int(re.sub("\D", "", number_of_user))
                    break
            else:
                continue
            break
    return movie_afisha_dict


def get_afisha_movie_year(movie):
    movie_link = movie.find(class_='m-disp-table').find("a")['href']
    response = requests.get("http:{}".format(movie_link))
    parsed_html = BeautifulSoup(response.text, 'html.parser')

    string_with_year = parsed_html.find(class_='m-margin-btm').find('span', class_='creation').get_text()

    if string_with_year.find('мин.') != -1:
        index_of_last_comma = string_with_year.rfind(',')
        string_with_year = string_with_year[:index_of_last_comma]
    index_of_year_starts = string_with_year.find('19')
    if index_of_year_starts == -1:
        index_of_year_starts = string_with_year.find('20')
    year = string_with_year[index_of_year_starts: index_of_year_starts + 4]
    return year


def sort_movies(movies, sorting_by):
    if sorting_by == 'cinema':
        sort_method = 'number_of_cinemas'
    else:
        sort_method = 'rating'

    sorted_by_dict = {}
    for key, value in movies.items():
        if value[sort_method] is None:
            continue
        sorted_by_dict[key] = value[sort_method]
    return sorted_by_dict, sort_method


def output_movies_to_console(movies, sorted_by_rating, value1):
    sorted_x = sorted(sorted_by_rating.items(), key=lambda x: x[1])
    sorted_x.reverse()
    print("Ten first movies sorted by {}:".format(value1.replace("_", " ")))
    print("Movie name, Rating, Number of users, Number of cinemas")
    for movie_name in sorted_x[0:10]:
        print("{0}, {1}, {2}, {3}".format(movie_name[0], movies[movie_name[0]]['rating'],
                                          movies[movie_name[0]]['users'], movies[movie_name[0]]['number_of_cinemas']))


def get_command_line_arguments():
    parser = argparse.ArgumentParser(description="'Sorting by' parameter.")
    parser.add_argument('-s', '--sort',
                        help='Will sort movies by "rating" or "cinema"(number of cinemas where movie is going).',
                        required=False)
    return parser.parse_args()

if __name__ == '__main__':
    args = get_command_line_arguments()
    sort_by_rating = args.sort
    movie_list_tags_afisha = get_afisha_movies_base_inform()
    movie_directory = parse_list_tags_movies_afisha(movie_list_tags_afisha)
    movies_info = fetch_movie_info(movie_directory)
    sorted_dict, text_value_of_sort_method = sort_movies(movies_info, sort_by_rating)
    output_movies_to_console(movies_info, sorted_dict, text_value_of_sort_method)
