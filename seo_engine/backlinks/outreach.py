class OutreachGenerator:
    def generate(self, prospect: dict, evaluation: dict, angle: str = "resource-page") -> str:
        name = prospect.get("website_name") or prospect.get("domain") or "there"
        title = prospect.get("page_title") or "your Rio travel resource"
        page_url = prospect.get("page_url") or ""
        target = evaluation.get("suggested_target_page") or "https://rioprivatedriver.com/"

        if angle == "guest-article":
            opening = f"I found {title} and its coverage of Rio travel."
            pitch = "I can contribute a practical, factual article focused on airport transfers and private transportation in Rio for English-speaking visitors."
        elif angle == "transportation":
            opening = f"I noticed {title} and the transportation information you provide for Rio travelers."
            pitch = "Your readers may find Rio Private Driver useful for English-speaking private airport transfers and local touring."
        elif angle == "partnership":
            opening = f"I came across {title} while researching useful Rio travel resources."
            pitch = "There may be a mutually useful partnership opportunity between your audience and Rio Private Driver's English-language private transportation service."
        else:
            opening = f"I came across {title} and found it useful for travelers researching Rio de Janeiro."
            pitch = f"Would you consider adding {target} as a useful transportation resource for visitors who need English-speaking private driver service?"

        return (
            f"Hello {name},\n\n"
            f"{opening}\n\n"
            f"{pitch}\n\n"
            f"The relevant page is {target}. "
            f"It would only be appropriate if it adds value for your readers: {page_url}.\n\n"
            "Please let me know if you think this is relevant.\n\nBest regards"
        )
