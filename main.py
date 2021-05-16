import followbot
import user
import config
from colorama import Fore, init
import re
import os
import pickle


# attention: bad code!
# but as long as it works, i don't care :P

os.system("cls" if os.name == "nt" else "clear")

init()
INFO = Fore.LIGHTBLUE_EX + "[*]" + Fore.BLUE
INPUT = Fore.LIGHTGREEN_EX + "[?] " + Fore.GREEN
SUCCESS = Fore.LIGHTGREEN_EX + "[+] " + Fore.GREEN
WARN = Fore.LIGHTYELLOW_EX + "[!]" + Fore.YELLOW
ERROR = Fore.LIGHTRED_EX + "[!]" + Fore.RED

yabkn = {
    True: Fore.GREEN + "Ya",
    False: Fore.RED + "Bukan"
}


def check_config():
    nullable_int = (int, type(None))
    error_msg = "Config tidak valid:"
    if type(config.min_followers) not in nullable_int:
        print(ERROR, error_msg, "min_followers")
    elif type(config.max_followers) not in nullable_int:
        print(ERROR, error_msg, "max_followers")
    elif type(config.email_verified) != bool:
        print(ERROR, error_msg, "email_verified")
    elif type(config.phone_verified) != bool:
        print(ERROR, error_msg, "phone_verified")
    elif type(config.official_shop) != bool:
        print(ERROR, error_msg, "official_shop")
    elif type(config.country) != bool:
        print(ERROR, error_msg, "country")
    elif type(config.work_recursively) != bool:
        print(ERROR, error_msg, "work_recursively")
    elif type(config.recursion_limit) != int:
        print(ERROR, error_msg, "recursion_limit")
    elif type(config.search_in_followers) != bool:
        print(ERROR, error_msg, "search_in_followers")
    elif type(config.search_in_following) != bool:
        print(ERROR, error_msg, "search_in_following")
    elif config.where not in ("mall shops", "flash sale", "target", "timeline"):
        print(ERROR, error_msg, "where")
    else:
        return
    exit(1)


def int_input(prompt_: str, max_: int = -1, min_: int = 1) -> int:
    input_: str
    while True:
        input_ = input(f"{INPUT}{prompt_}{Fore.RESET}")
        if input_.isdigit():
            input_int = int(input_)
            if max_ == -1:
                return input_int
            elif min_ <= input_int <= max_:
                return input_int
            elif input_int > max_:
                print(ERROR, "Angka terlalu banyak!")
                continue
            elif input_int < min_:
                print(ERROR, "Angka terlalu sedikit!")
                continue
        print(ERROR, "Masukkan angka!")


def in_range(min_: int, max_: int, num: int) -> bool:
    if min_ is not None and max_ is not None:
        return min_ <= num <= max_
    elif min_ is None and max_ is not None:
        return num <= max_
    elif max_ is None and min_ is not None:
        return min_ <= num
    return True


def get_targets() -> list:
    with open("target.txt", 'r') as f:
        split = f.read().split("\n")
        return [match.group(1) for url in split
                if (match := re.search(r"shopee\.co\.id/(.*)\?", url)) is not None]


check_config()
with open("cookie", 'rb') as f:
    print(INFO, "Mengambil informasi user...", end="\r")
    u: user.User = user.User.login(pickle.load(f))

exclude = set([x.shopid for x in followbot.FollowBot.get_shop_following(u.shopid)])
def work(shopids_or_usernames: list, depth: int = 1):  # no idea for a name
    for item in set(shopids_or_usernames):
        print(INFO, "Mengambil informasi akun...")
        if type(item) == int:  # shopid
            if (shop_info := followbot.FollowBot.get_shop_info(item)) is None:
                continue
            shop = followbot.FollowBot.get_shop_detail(shop_info.account.username)
        else:  # username
            shop = followbot.FollowBot.get_shop_detail(item)

        if item in exclude or shop.followed:
            print(WARN, "Akun", shop.account.username, "sudah difollow")
            continue
        must_follow = in_range(config.min_followers, config.max_followers, shop.follower_count)

        if must_follow and config.email_verified:
            must_follow = shop.account.email_verified
        if must_follow and config.phone_verified:
            must_follow = shop.account.phone_verified
        if must_follow and config.official_shop:
            must_follow = shop.is_official_shop
        if must_follow and config.country:
            must_follow = shop.country == "ID"

        print(Fore.BLUE, "\tNama:" + Fore.RESET, shop.name)
        print(Fore.BLUE, "\tJumlah Follower:" + Fore.RESET, shop.follower_count)
        print(Fore.BLUE, "\tToko Resmi:" + Fore.RESET, yabkn[shop.is_official_shop])
        print(Fore.BLUE, "\tUsername:" + Fore.RESET, shop.account.username)
        print(Fore.BLUE, "\tFollowing:" + Fore.RESET, shop.account.following_count)

        if must_follow:
            print(SUCCESS, "Following", shop.name)
            bot.follow(shop.shopid)
        else:
            print(WARN, "Akun tidak memenuhi syarat, Skip...")
        exclude.add(item)

        if config.work_recursively:
            if depth+1 >= config.recursion_limit:
                print(WARN, "Recursion limit")
                continue
            if config.search_in_followers:
                print(INFO, "Mencari di follower", shop.account.username)
                work([follower.shopid for follower in followbot.FollowBot.get_shop_followers(shop.shopid)], depth+1)
            if config.search_in_following:
                print(INFO, "Mencari di akun yang diikuti oleh", shop.account.username)
                work([follower.shopid for follower in followbot.FollowBot.get_shop_following(shop.shopid)], depth+1)
    print(SUCCESS, "Pencarian selesai")


print(INFO, "Welcome", u.username, " " * 10)
bot = followbot.FollowBot(u)

if config.where == "mall shops":
    limit = int_input("Masukkan limit akun untuk difollow: ")
    targets = followbot.FollowBot.get_mall_shops(limit)
    print(INFO, "Mengambil id akun...")
    work(targets)
elif config.where == "flash sale":
    limit = int_input("Masukkan limit akun untuk difollow: ")
    targets = followbot.FollowBot.get_shopids_from_flashsale(limit=limit)
    print(INFO, "Mengambil id akun...")
    work(targets)
elif config.where == "timeline":
    targets = bot.get_random_user_from_timeline()
    print(INFO, "Mengambil id akun...")
    work(targets)
elif config.where == "target":
    targets = get_targets()
    print(INFO, "Mengambil id akun...")
    work([followbot.FollowBot.get_shop_detail(uname).shopid for uname in targets])
else:
    print(ERROR, "Konfigurasi error")
    exit(1)
