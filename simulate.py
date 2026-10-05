from agents.always_duke import AlwaysDuke
from agents.honest_random import HonestRandom
from agents.random_agent import RandomAgent
from agents.passive_agent import PassiveAgent
from agents.weighted_param_bot import WeightedParamBot
from agents.weighted_param_bot_v2 import WeightedParamBotV2
from agents.adaptive_weighted_bot import AdaptiveGenome, AdaptiveWeightedBot
from src.game import Game

import random

def main():
    # players = [
    #     WeightedParamBot("1", "Anti-PassiveAgent", 
    #                      bluff_percent=0.5,
    #                      challenge_percent=0.5,
    #                      income_weight= 0.49577042683363554,
    #                      foreign_aid_weight=0.6822759904371777,
    #                      coup_weight=1.3664507026090351,
    #                      tax_weight=0.602641812582586,
    #                      assassinate_weight=2.3416001150134598,
    #                      exchange_weight=0.17586871034649856,
    #                      steal_weight=1.8635749319614827,
    #                      print_turns=False
    #                      ),
    #     PassiveAgent("2", "PassiveAgent", print_turns=False),
    #     PassiveAgent("3", "PassiveAgent", print_turns=False),
    #     PassiveAgent("4", "PassiveAgent", print_turns=False),
    # ]

    # BEST_GENOME = AdaptiveGenome(
    #     action_weights={'income': {'bias': -0.13188057742059917, 'own_coins': 0.9685085788269163, 'own_coins_high': -0.18199031513119873, 'own_influence': -0.13144870612444662, 'opponent_coins': -0.4078003455457521, 'opponent_influence': -0.10520941906436947, 'coin_advantage': -0.45459461410681423, 'influence_advantage': 0.18170880863324027, 'living_opponents': -0.03733423119961142, 'opponent_one_influence': 0.3474121537341395, 'self_one_influence': 0.06789449485597414, 'can_coup': 0.34355760966818766, 'can_assassinate': -0.2997531240136645, 'turn_progress': -0.5115894246823782, 'game_length': -1.8793475009960805}, 'foreign_aid': {'bias': 0.49461370744934524, 'own_coins': 0.12826477864785224, 'own_coins_high': -0.33358853663204163, 'own_influence': -1.5905508849053185, 'opponent_coins': -0.017146735280595904, 'opponent_influence': -0.056394809319661274, 'coin_advantage': 0.5451203538187847, 'influence_advantage': -0.4710738707418825, 'living_opponents': 0.12021984336599317, 'opponent_one_influence': -0.4691132944222927, 'self_one_influence': -0.3746816644010397, 'can_coup': 0.719295586149783, 'can_assassinate': -0.3476596320931876, 'turn_progress': 0.19525262045851086, 'game_length': 0.542290932379716}, 'coup': {'bias': -0.11549925108849703, 'own_coins': -0.383199233484124, 'own_coins_high': -0.3531892767015138, 'own_influence': -0.02413792845398141, 'opponent_coins': -0.3382405637708006, 'opponent_influence': -0.36468142625290206, 'coin_advantage': 0.35383835424098653, 'influence_advantage': 0.1698062253012439, 'living_opponents': 0.09244913799169652, 'opponent_one_influence': 0.2195781515499093, 'self_one_influence': -0.39332715289738235, 'can_coup': 0.8593924418715009, 'can_assassinate': 0.6409395448651707, 'turn_progress': -0.36353691675697886, 'game_length': -0.39772240430783284}, 'tax': {'bias': 0.988645300837983, 'own_coins': -0.02851676895595974, 'own_coins_high': -0.17192238947047955, 'own_influence': -0.20564802617815425, 'opponent_coins': -0.4403344587130689, 'opponent_influence': -0.19704496850103848, 'coin_advantage': 1.2578933308419507, 'influence_advantage': -1.2110905141542971, 'living_opponents': -0.20522446690352175, 'opponent_one_influence': -0.2439086680832731, 'self_one_influence': 0.1603914830601329, 'can_coup': 0.14091139119720428, 'can_assassinate': 0.1953215419628777, 'turn_progress': 0.4577959436616329, 'game_length': -1.0315634002972236}, 'assassinate': {'bias': 0.5544929211480656, 'own_coins': -0.263605695943668, 'own_coins_high': 0.9715978612039491, 'own_influence': 0.3506595332442107, 'opponent_coins': 0.9363281953620675, 'opponent_influence': 0.181424139076888, 'coin_advantage': 0.6546805779062201, 'influence_advantage': 0.27241601123473697, 'living_opponents': 0.446815561170345, 'opponent_one_influence': 0.658530317400344, 'self_one_influence': 0.12508910809287888, 'can_coup': 0.14703087487576832, 'can_assassinate': -0.06657827735752529, 'turn_progress': -0.7501009645221441, 'game_length': 0.4683637500109231}, 'exchange': {'bias': -1.1810413229972199, 'own_coins': -0.4504501058046876, 'own_coins_high': -0.8751019360848028, 'own_influence': -0.2608387333578059, 'opponent_coins': 0.37993249649015526, 'opponent_influence': -0.48324074517052257, 'coin_advantage': -0.9193706244360087, 'influence_advantage': -0.5048000315007627, 'living_opponents': 0.13465530800716452, 'opponent_one_influence': -0.14755207640618348, 'self_one_influence': 0.17926314277873365, 'can_coup': 0.3914413570571487, 'can_assassinate': 0.3845855578960816, 'turn_progress': 0.06546605141938061, 'game_length': -0.5111752395910596}, 'steal': {'bias': 0.6190274191773419, 'own_coins': 0.3985491596236381, 'own_coins_high': 0.04281227547559473, 'own_influence': -0.3733490491702633, 'opponent_coins': 1.5019586937928335, 'opponent_influence': 0.007441570231860803, 'coin_advantage': 0.8743672855558368, 'influence_advantage': 0.15665303984419565, 'living_opponents': 0.3969673855204583, 'opponent_one_influence': 0.04054046366454728, 'self_one_influence': 0.8257748133598183, 'can_coup': 0.09231036059819688, 'can_assassinate': 0.7923533764470281, 'turn_progress': -0.48480155575050077, 'game_length': 0.5940460184943988}},
    #     bluff_weights={'bias': 0.3638929165164544, 'own_coins': 1.8276010337143862, 'own_coins_high': -0.9091892703935989, 'own_influence': -0.41138440457666203, 'opponent_coins': 0.08379806713673948, 'opponent_influence': -1.425430831532449, 'coin_advantage': 0.19311775656217825, 'influence_advantage': 1.8255665607496547, 'living_opponents': 1.4465411483286648, 'opponent_one_influence': 1.057054346958223, 'self_one_influence': 0.8980543887002601, 'can_coup': 1.4060518077031687, 'can_assassinate': 0.29457174433349764, 'turn_progress': -0.2667863417285208, 'game_length': 0.8718013467999888},
    #     challenge_weights={'bias': 1.15209166691903, 'own_coins': 0.3022942729239443, 'own_coins_high': 0.8783410661120312, 'own_influence': 0.06133225176022527, 'opponent_coins': -0.16103019715905287, 'opponent_influence': -0.4208462356930397, 'coin_advantage': 1.1652990328177788, 'influence_advantage': 0.4655238132164156, 'living_opponents': -0.10856451077060894, 'opponent_one_influence': 1.1779841864121263, 'self_one_influence': 0.3680772219135846, 'can_coup': 0.1596624047815471, 'can_assassinate': -0.2270081633031917, 'turn_progress': 1.6157617568085838, 'game_length': 0.24701161474513644},
    #     block_weights={'bias': 0.03334135342107028, 'own_coins': 0.5473493478733844, 'own_coins_high': 0.753048096737344, 'own_influence': 1.9485922711859796, 'opponent_coins': 0.4553099609400154, 'opponent_influence': 0.89362796549858, 'coin_advantage': -0.3966132482556781, 'influence_advantage': -0.014995480474131795, 'living_opponents': 0.3042269147097566, 'opponent_one_influence': 0.9811269679835153, 'self_one_influence': 0.1371906241526974, 'can_coup': -0.11220136580516872, 'can_assassinate': -0.5313796289864607, 'turn_progress': -0.17519197693966393, 'game_length': -0.431639822087046},
    #     target_weights={'bias': -1.187631957767691, 'opponent_coins': 0.39756244194027146, 'opponent_influence': 0.48746600592793754, 'coin_advantage': 1.351722132635217, 'influence_advantage': 0.08518671797778546, 'one_influence': 0.5749173165176825},
    # )

    BEST_GENOME = AdaptiveGenome(
    action_weights={'income': {'bias': -0.8168316020822466, 'own_coins': 0.37369251580405993, 'own_coins_high': -0.04567721848295825, 'own_influence': -0.8059352515551135, 'opponent_coins': 0.17821677968651597, 'opponent_influence': -0.37620929946252735, 'coin_advantage': 0.7525425182914607, 'influence_advantage': -0.2978980910350252, 'living_opponents': 0.2664998644521428, 'opponent_one_influence': 0.19199802119244444, 'self_one_influence': 0.14970863574894883, 'can_coup': -0.33125575564188137, 'can_assassinate': 0.1558543147273636, 'turn_progress': -0.34918742511071715, 'game_length': 0.45385941476799974}, 'foreign_aid': {'bias': 0.5664691008053447, 'own_coins': 0.1489861526210185, 'own_coins_high': -0.04654471235092107, 'own_influence': -0.060922033730288636, 'opponent_coins': 0.9962658032528268, 'opponent_influence': 1.5941619075223823, 'coin_advantage': 1.066766993498803, 'influence_advantage': 0.1762613461723931, 'living_opponents': 0.09595123566418418, 'opponent_one_influence': 0.8012291576940849, 'self_one_influence': 1.197426345571909, 'can_coup': 0.10347785168565504, 'can_assassinate': 0.8165269450943806, 'turn_progress': 0.8241226729715374, 'game_length': -0.46665310358230305}, 'coup': {'bias': -0.5424352679106411, 'own_coins': -0.26066876132215516, 'own_coins_high': 0.08749709144647594, 'own_influence': 0.33953301404373193, 'opponent_coins': 0.07628644574754118, 'opponent_influence': -0.33355303330605157, 'coin_advantage': 0.05637182829559844, 'influence_advantage': -0.1314325049125148, 'living_opponents': 0.059152134254204236, 'opponent_one_influence': -0.29307278398001063, 'self_one_influence': -0.5077427796709358, 'can_coup': 0.05702072138407282, 'can_assassinate': -0.5254750010122391, 'turn_progress': -0.655638954312807, 'game_length': 0.5274658943182421}, 'tax': {'bias': 0.789668561477868, 'own_coins': 0.5532311732881142, 'own_coins_high': 0.6076353004524906, 'own_influence': -0.6200490736626647, 'opponent_coins': -0.6957004896679477, 'opponent_influence': -0.3191984361151803, 'coin_advantage': 1.267654119421072, 'influence_advantage': 0.5282398626614085, 'living_opponents': 0.5557032131004801, 'opponent_one_influence': 0.2021191066133869, 'self_one_influence': 0.5579404253499715, 'can_coup': 0.16954069453699078, 'can_assassinate': 0.2649058551213122, 'turn_progress': 0.575861741969401, 'game_length': 0.7070736907411442}, 'assassinate': {'bias': 0.25056482858781304, 'own_coins': 0.32565824195043047, 'own_coins_high': 1.0220222458630435, 'own_influence': 0.3349829802426924, 'opponent_coins': 0.2426002527128605, 'opponent_influence': 0.783029814238748, 'coin_advantage': -0.1824878484975948, 'influence_advantage': 0.7204312776994917, 'living_opponents': 0.4937390308502241, 'opponent_one_influence': 0.8980234862687971, 'self_one_influence': -0.08420125442274357, 'can_coup': 1.1095725551299733, 'can_assassinate': 1.132739836101891, 'turn_progress': -0.3464055366546023, 'game_length': 0.6473957508522802}, 'exchange': {'bias': -0.6629281421046421, 'own_coins': 0.10782672098785455, 'own_coins_high': -0.5661412695722626, 'own_influence': 0.9366938656648027, 'opponent_coins': 0.5207529827871543, 'opponent_influence': -0.21184599928255524, 'coin_advantage': -0.5065311301683455, 'influence_advantage': 0.6371042912824337, 'living_opponents': 0.8238231523762529, 'opponent_one_influence': -0.14007018935174198, 'self_one_influence': -1.2492211795851373, 'can_coup': -0.48098951649678623, 'can_assassinate': 0.4503486775496601, 'turn_progress': 0.125832124831654, 'game_length': 0.5274285031836017}, 'steal': {'bias': 1.2008562679656087, 'own_coins': -1.1722144636795178, 'own_coins_high': -0.2756984518819384, 'own_influence': -0.6841588546627527, 'opponent_coins': -0.6705092240408763, 'opponent_influence': -0.5426164763070926, 'coin_advantage': -0.07891090794736312, 'influence_advantage': -0.5975106095410191, 'living_opponents': -0.4161663343778758, 'opponent_one_influence': 0.6928665260961163, 'self_one_influence': 0.27496634044613216, 'can_coup': -0.26583574310123975, 'can_assassinate': -0.27100553632302354, 'turn_progress': 0.42624523570303474, 'game_length': 0.30408213733491946}},
    bluff_weights={'bias': -1.68807266055679, 'own_coins': 0.956238436632093, 'own_coins_high': 0.013054236333343017, 'own_influence': -0.3209949888600948, 'opponent_coins': 0.12414487316777678, 'opponent_influence': 0.6275693500461477, 'coin_advantage': 1.144484326210227, 'influence_advantage': 0.9087686658951335, 'living_opponents': -0.1395001474242984, 'opponent_one_influence': -1.1735883767699158, 'self_one_influence': 0.8593295846192611, 'can_coup': -0.7133108678551121, 'can_assassinate': -1.134759293345821, 'turn_progress': -1.1910963648193227, 'game_length': 1.0411645698371885},
    challenge_weights={'bias': 1.7626018551553089, 'own_coins': 2.033752747732989, 'own_coins_high': 0.9761901106964976, 'own_influence': -0.6325587436132727, 'opponent_coins': 0.3146837021121702, 'opponent_influence': 1.1366317079359898, 'coin_advantage': 0.4661943766236824, 'influence_advantage': 0.6312963272241665, 'living_opponents': 1.1842810230217686, 'opponent_one_influence': 1.0163774691644016, 'self_one_influence': 0.26115347367699293, 'can_coup': 0.33204673430614795, 'can_assassinate': 0.4469025770177361, 'turn_progress': -0.742635738830218, 'game_length': 0.029525005287406283},
    block_weights={'bias': -0.023790457423572258, 'own_coins': -1.000818026932278, 'own_coins_high': 0.16502071135917876, 'own_influence': 0.14595284194970432, 'opponent_coins': -0.45146255971475047, 'opponent_influence': 0.9163389108670913, 'coin_advantage': -0.018473899433131463, 'influence_advantage': -0.49377160978500134, 'living_opponents': 0.43095326994750804, 'opponent_one_influence': -0.9790320119211313, 'self_one_influence': 0.7036677440715875, 'can_coup': -0.7388682420474428, 'can_assassinate': 0.7846035482031708, 'turn_progress': -0.7328603491770099, 'game_length': -0.8404898218861083},
    target_weights={'bias': -0.2973651469063693, 'opponent_coins': -0.7051755050896108, 'opponent_influence': 0.8840619424153078, 'coin_advantage': 0.09962279549745737, 'influence_advantage': -0.9140682882801257, 'one_influence': -0.5645685676569591},
)

    players = [
            AdaptiveWeightedBot("1", "Anti-AlwaysDuke",
                            genome=BEST_GENOME,
                            print_turns=False
                            ),
            AlwaysDuke("2", "AlwaysDuke Agent 1", print_turns=False),
            # AlwaysDuke("3", "AlwaysDuke Agent 2", print_turns=False),
            # AlwaysDuke("4", "AlwaysDuke Agent 3", print_turns=False),
            # AlwaysDuke("5", "AlwaysDuke Agent 4", print_turns=False),
            # AlwaysDuke("6", "AlwaysDuke Agent 5", print_turns=False)
        ]

    winners = {players[i].name: 0 for i in range(len(players))}
    order = {players[i].name: [0 for i in range(len(players))] for i in range(len(players))}
    games = 50000
    for i in range(games):
        random.shuffle(players)
        for j in range(len(players)):
            order[players[j].name][j] += 1
        game = Game(players)

        while game.winner is None:
            player = game.current

            player.choose_action(game)

        winners[game.winner.name] += 1

        if (i+1)%500==0:
            print(f"\n{i+1}/{games}")
            print("Win percentages")
            for k in winners:
                print(f"{k}: {winners[k]/(i+1)}")

    print("\nNumber of wins:", winners)
    print("Turn order Amounts:", order)
    print("Win percentages")
    for i in winners:
        print(f"{i}: {winners[i]/games}")


if __name__ == "__main__":
    main()